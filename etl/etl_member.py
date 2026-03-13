"""Üye CRUD işlemlerini içeren ETL stored procedure'leri.

Her fonksiyon (bool/int, str) veya (df | None, str) döner.
"""

import uuid
from datetime import datetime

import pandas as pd

from constants import (
    SHEET_NAME, HISTORY_WS, STAGING_WS,
    HISTORY_COLUMNS, VALID_TO_OPEN, REPORT_DATETIME_FMT,
)
from utils.date_utils import parse_report_datetime, format_report_datetime
from utils.transforms import (
    clean_name, clean_phone, clean_city, clean_school,
    get_next_uye_no,
)
from utils.db_utils import get_data, append_data, update_row_data


# ---------------------------------------------------------------------------
# Yardımcı
# ---------------------------------------------------------------------------

def _now() -> str:
    """Raporda kullanılan formatta: DD.MM.YYYY HH:MM:SS"""
    return datetime.now().strftime(REPORT_DATETIME_FMT)


def _ensure_columns(df: pd.DataFrame) -> pd.DataFrame:
    """HISTORY_COLUMNS sırasını garantiler; eksik kolonları boş string ile doldurur."""
    for col in HISTORY_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[HISTORY_COLUMNS]


def _active_record(df_history: pd.DataFrame, uye_no: int):
    """Verilen uye_no için aktif satırın (target_index, series) çiftini döner."""
    df_history = df_history.copy()
    df_history['is_active_str'] = df_history['is_active'].astype(str).str.strip().str.upper()
    df_history['uye_no_int'] = pd.to_numeric(df_history['uye_no'], errors='coerce').fillna(0).astype(int)
    mask = (df_history['uye_no_int'] == int(uye_no)) & (df_history['is_active_str'] == 'TRUE')
    if not mask.any():
        return None, None
    idx = df_history[mask].index[0]
    return idx, df_history.loc[[idx]].copy()


# ---------------------------------------------------------------------------
# ETL: Extract + Transform  (veritabanına YAZMAZ)
# ---------------------------------------------------------------------------

def sp_extract_preview():
    """
    Staging'den yeni kayıtları çeker ve temizler; veritabanına yazmaz.
    Döner: (df_preview | None, mesaj)
    """
    df_staging = get_data(SHEET_NAME, STAGING_WS)
    df_history = get_data(SHEET_NAME, HISTORY_WS)

    if df_staging.empty:
        return None, "Staging tablosunda işlenecek veri yok."

    # Zaman damgasına göre yeni kayıtları filtrele
    if not df_history.empty and 'ilk_kayit_tarihi' in df_history.columns:
        existing_ts = df_history['ilk_kayit_tarihi'].tolist()
        df_new = df_staging[~df_staging['Zaman damgası'].isin(existing_ts)].copy()
    else:
        df_new = df_staging.copy()

    if df_new.empty:
        return None, "İçeri alınacak yeni bir kayıt bulunamadı."

    # Telefon ile çoklama kontrolü
    phone_col = 'Telefon Numaranız? (Başında 0 olmadan boşluksuz yazınız)'
    df_new['temiz_telefon'] = df_new[phone_col].apply(clean_phone)
    df_new = df_new.drop_duplicates(subset=['temiz_telefon'], keep='last')

    if not df_history.empty and 'telefon' in df_history.columns:
        existing_phones = df_history['telefon'].astype(str).tolist()
        df_new = df_new[~df_new['temiz_telefon'].isin(existing_phones)]

    if df_new.empty:
        return None, "Yeni kayıtlar bulundu ancak hepsi sistemde zaten mevcut. 🛡️"

    # En erken kaydolan 1001 alır; timestamp'e göre eskiden yeniye sırala (dayfirst=True)
    df_new['zaman_dt'] = parse_report_datetime(df_new['Zaman damgası'])
    df_new = df_new.sort_values('zaman_dt', ascending=True).reset_index(drop=True)

    next_no = get_next_uye_no(df_history)
    records = []

    for _, row in df_new.iterrows():
        ts_dt = parse_report_datetime(row['Zaman damgası'])
        ilk_kayit = format_report_datetime(ts_dt) if pd.notna(ts_dt) else str(row['Zaman damgası'])
        records.append({
            'uye_sk':             str(uuid.uuid4()),
            'uye_no':             next_no,
            'ilk_kayit_tarihi':   ilk_kayit,
            'ad':                 clean_name(row.get('Adınız?', '')),
            'soyad':              clean_name(row.get('Soyadınız?', '')),
            'email':              str(row.get('E-Posta Adresiniz?', '')).strip(),
            'telefon':            row['temiz_telefon'],
            'dogum_tarihi':       str(row.get('Doğum Tarihiniz?', '')).strip(),
            'yasadigi_sehir':     clean_city(row.get('Yaşadığınız Şehir?', '')),
            'uyesi_oldugu_sehir': clean_city(row.get('Üyesi olduğunuz şehir?', '')),
            'cinsiyet':           str(row.get('Cinsiyetiniz?', '')).strip(),
            'egitim_durumu':      str(row.get('Eğitim Durumunuz?', '')).strip(),
            'universite':         clean_school(row.get('Okuduğunuz Üniversite? (Okulunuz Tam İsmini Yazınız)', '')),
            'bolum':              clean_school(row.get('Bölümünüz? (Bölümüzün Tam İsmini Yazınız)', '')),
            'sinif':              str(row.get('Sınıfınız?', '')).strip(),
            'rol':                str(row.get('Rolünüz?', 'Üye')).strip(),
            'notlar':             str(row.get('Bize Notunuz (Ek öneri ve taleplerinizi buradan iletebilirsiniz.)', '')).strip(),
            'valid_from':         ilk_kayit,
            'valid_to':           VALID_TO_OPEN,
            'is_active':          True,
            'islenme_tarihi':     '',  # Load aşamasında doldurulacak
        })
        next_no += 1

    df_preview = pd.DataFrame(records)
    return df_preview, f"✅ {len(df_preview)} yeni kayıt bulundu. İnceleyip düzenledikten sonra yükleyebilirsiniz."


# ---------------------------------------------------------------------------
# ETL: Load  (önizleme DataFrame'ini veritabanına yazar)
# ---------------------------------------------------------------------------

def sp_load_to_history(df_preview: pd.DataFrame):
    """
    sp_extract_preview() çıktısını (kullanıcı düzenlemesiyle) Dim_Member_History'e yazar.
    Döner: (count, mesaj)
    """
    df = df_preview.copy()
    df['islenme_tarihi'] = _now()
    df = _ensure_columns(df)
    append_data(SHEET_NAME, HISTORY_WS, df)
    return len(df), f"🎉 {len(df)} kayıt başarıyla veritabanına yüklendi!"


# ---------------------------------------------------------------------------
# Legacy tek adımlı ETL  (geriye dönük uyumluluk)
# ---------------------------------------------------------------------------

def sp_staging_to_history():
    df_preview, msg = sp_extract_preview()
    if df_preview is None:
        return 0, msg
    count, load_msg = sp_load_to_history(df_preview)
    return count, load_msg


# ---------------------------------------------------------------------------
# Üye güncelleme (SCD1 / SCD2)
# ---------------------------------------------------------------------------

def sp_update_member(
    uye_no: int,
    updated_fields: dict,
    is_correction: bool = False,
    effective_date=None,          # datetime.date | None  (SCD2 için geçerlilik tarihi)
):
    """
    is_correction=True  → SCD Tip 1: mevcut satırı üstüne yazar (hata düzeltme).
    is_correction=False → SCD Tip 2: eski kaydı kapatır, yeni satır açar.

    effective_date: SCD2 değişikliğinin gerçekleştiği tarih.
      - None verilirse "şu an" kullanılır.
      - Geçmiş tarih verilebilir (örn. Şubat'ta yapılmış değişikliği Mart'ta girmek).
    """
    from datetime import date as _date, datetime as _datetime

    df_history = get_data(SHEET_NAME, HISTORY_WS)
    target_index, old_record = _active_record(df_history, uye_no)

    if old_record is None:
        return False, "Kişinin aktif kaydı bulunamadı."

    now_str = _now()

    # effective_date → transition_str (SCD2 geçiş zamanı)
    if effective_date is not None and isinstance(effective_date, _date):
        transition_str = _datetime.combine(effective_date, _datetime.min.time()).strftime(REPORT_DATETIME_FMT)
    else:
        transition_str = now_str

    if is_correction:
        for key, value in updated_fields.items():
            old_record[key] = value
        old_record['islenme_tarihi'] = now_str
        old_record = _ensure_columns(old_record)
        update_row_data(SHEET_NAME, HISTORY_WS, target_index, old_record)
        return True, "Sehven yapılan hata düzeltildi, tarihçe oluşturulmadı. 🛠️"

    # SCD2: eski kaydı kapat
    old_record['valid_to']       = transition_str
    old_record['is_active']      = False
    old_record['islenme_tarihi'] = now_str
    old_record = _ensure_columns(old_record)
    update_row_data(SHEET_NAME, HISTORY_WS, target_index, old_record)

    # Yeni satır aç
    new_record = old_record.copy()
    new_record['uye_sk']         = str(uuid.uuid4())
    for key, value in updated_fields.items():
        new_record[key] = value
    new_record['valid_from']     = transition_str
    new_record['valid_to']       = VALID_TO_OPEN
    new_record['is_active']      = True
    new_record['islenme_tarihi'] = now_str
    new_record = _ensure_columns(new_record)
    append_data(SHEET_NAME, HISTORY_WS, new_record)

    tarih_notu = f" (geçerlilik: {transition_str[:10]})" if effective_date else ""
    return True, f"Yeni bilgiler SCD2 formatında kaydedildi{tarih_notu}! 📝"


# ---------------------------------------------------------------------------
# Manuel üye ekleme
# ---------------------------------------------------------------------------

def sp_insert_manual_member(form_data: dict):
    """Arayüzden girilen manuel kayıtları SCD2 standardında ekler."""
    df_history = get_data(SHEET_NAME, HISTORY_WS)

    temiz_tel = clean_phone(form_data.get('telefon', ''))
    if not df_history.empty and 'telefon' in df_history.columns:
        existing_phones = df_history['telefon'].astype(str).tolist()
        if temiz_tel in existing_phones and temiz_tel != "":
            return False, "Bu telefon numarası ile sistemde zaten kayıtlı bir kişi var! 🛡️"

    next_no = get_next_uye_no(df_history)
    now_str = _now()

    new_record = {
        'uye_sk':             str(uuid.uuid4()),
        'uye_no':             next_no,
        'ilk_kayit_tarihi':   now_str,
        'ad':                 clean_name(form_data.get('ad', '')),
        'soyad':              clean_name(form_data.get('soyad', '')),
        'email':              str(form_data.get('email', '')).strip(),
        'telefon':            temiz_tel,
        'dogum_tarihi':       str(form_data.get('dogum_tarihi', '')).strip(),
        'yasadigi_sehir':     clean_city(form_data.get('yasadigi_sehir', '')),
        'uyesi_oldugu_sehir': clean_city(form_data.get('uyesi_oldugu_sehir', '')),
        'cinsiyet':           str(form_data.get('cinsiyet', '')).strip(),
        'egitim_durumu':      str(form_data.get('egitim_durumu', '')).strip(),
        'universite':         clean_school(form_data.get('universite', '')),
        'bolum':              clean_school(form_data.get('bolum', '')),
        'sinif':              str(form_data.get('sinif', '')).strip(),
        'rol':                str(form_data.get('rol', 'Üye')).strip(),
        'notlar':             str(form_data.get('notlar', '')).strip(),
        'valid_from':         now_str,
        'valid_to':           VALID_TO_OPEN,
        'is_active':          True,
        'islenme_tarihi':     now_str,
    }

    df = _ensure_columns(pd.DataFrame([new_record]))
    append_data(SHEET_NAME, HISTORY_WS, df)
    return True, f"Kişi manuel olarak başarıyla eklendi! Yeni Üye No: {next_no} 🎉"


# ---------------------------------------------------------------------------
# Üye deaktivasyonu (Soft Delete)
# ---------------------------------------------------------------------------

def sp_deactivate_member(uye_no: int):
    """Kişiyi pasife alır. valid_to = şimdiki an, is_active = False."""
    df_history = get_data(SHEET_NAME, HISTORY_WS)
    target_index, old_record = _active_record(df_history, uye_no)

    if old_record is None:
        return False, "Kişinin aktif kaydı bulunamadı."

    now_str = _now()
    old_record['valid_to'] = now_str
    old_record['is_active'] = False
    old_record['islenme_tarihi'] = now_str
    old_record = _ensure_columns(old_record)

    update_row_data(SHEET_NAME, HISTORY_WS, target_index, old_record)
    return True, "Kişi başarıyla pasife alındı. Kayıt kapatıldı! 🛑"

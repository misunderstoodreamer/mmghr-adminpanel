import pandas as pd
import uuid
from datetime import datetime
import re
from db_utils import get_data, append_data

# --- TRANSFORMASYON FONKSİYONLARI ---

def clean_name(text):
    if pd.isna(text): return ""
    return str(text).strip().title()

def clean_phone(text):
    if pd.isna(text): return ""
    num = re.sub(r'\D', '', str(text))
    if num.startswith('0'):
        num = num[1:]
    if num.startswith('90') and len(num) == 12:
        num = num[2:]
    return num

def clean_city(text):
    if pd.isna(text): return ""
    return str(text).title().replace(" ", "")

def clean_school(text):
    if pd.isna(text): return ""
    return str(text).strip().title()

# --- ANA ETL SÜRECİ ---

def sp_staging_to_history():
    df_staging = get_data("gencmmg_db", "Staging_Form")
    df_history = get_data("gencmmg_db", "Dim_Member_History")

    if df_staging.empty:
        return 0, "Staging tablosunda işlenecek veri yok."

    # 1. ZAMAN DAMGASI İLE YENİ KAYITLARI BULMA
    if not df_history.empty and 'ilk_kayit_tarihi' in df_history.columns:
        existing_timestamps = df_history['ilk_kayit_tarihi'].tolist()
        df_new = df_staging[~df_staging['Zaman damgası'].isin(existing_timestamps)].copy()
    else:
        df_new = df_staging.copy()

    if df_new.empty:
        return 0, "İçeri alınacak yeni bir kayıt bulunamadı."

    # 2. TELEFON İLE ÇOKLAMA KONTROLÜ
    phone_col = 'Telefon Numaranız? (Başında 0 olmadan boşluksuz yazınız)'
    df_new['temiz_telefon'] = df_new[phone_col].apply(clean_phone)
    df_new = df_new.drop_duplicates(subset=['temiz_telefon'], keep='last')
    
    if not df_history.empty and 'telefon' in df_history.columns:
        existing_phones = df_history['telefon'].astype(str).tolist()
        df_new = df_new[~df_new['temiz_telefon'].isin(existing_phones)]
        
    if df_new.empty:
        return 0, "Yeni kayıtlar bulundu ancak hepsi sistemde zaten mevcut. 🛡️"

    # 3. İŞ KİMLİĞİ (BUSINESS KEY) ATAMA
    start_no = 1001
    if not df_history.empty and 'uye_no' in df_history.columns:
        existing_nos = pd.to_numeric(df_history['uye_no'], errors='coerce').dropna()
        if not existing_nos.empty:
            start_no = int(existing_nos.max()) + 1

    # 4. SATIR SATIR İŞLEME VE SCD2 FORMATINA ÇEVİRME
    records_to_append = []
    
    # GETDATE() muadili: Kodun/ETL'in çalıştığı tam an
    islenme_tarihi = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    valid_to = '2099-12-31' # Ucu açık (açık kayıtlar için standart DWH yaklaşımı)

    for _, row in df_new.iterrows():
        ilk_kayit = str(row['Zaman damgası'])
        
        new_record = {
            'uye_sk': str(uuid.uuid4()),
            'uye_no': start_no,
            'ilk_kayit_tarihi': ilk_kayit,
            'ad': clean_name(row.get('Adınız?', '')),
            'soyad': clean_name(row.get('Soyadınız?', '')),
            'email': str(row.get('E-Posta Adresiniz?', '')).strip(),
            'telefon': row['temiz_telefon'], 
            'dogum_tarihi': str(row.get('Doğum Tarihiniz?', '')).strip(),
            'yasadigi_sehir': clean_city(row.get('Yaşadığınız Şehir?', '')),
            'uyesi_oldugu_sehir': clean_city(row.get('Üyesi olduğunuz şehir?', '')),
            'cinsiyet': str(row.get('Cinsiyetiniz?', '')).strip(),
            'egitim_durumu': str(row.get('Eğitim Durumunuz?', '')).strip(),
            'universite': clean_school(row.get('Okuduğunuz Üniversite? (Okulunuz Tam İsmini Yazınız)', '')),
            'bolum': clean_school(row.get('Bölümünüz? (Bölümüzün Tam İsmini Yazınız)', '')),
            'sinif': str(row.get('Sınıfınız?', '')).strip(),
            'rol': str(row.get('Rolünüz?', 'Üye')).strip(), 
            'notlar': str(row.get('Bize Notunuz (Ek öneri ve taleplerinizi buradan iletebilirsiniz.)', '')).strip(),
            
            # YENİ SCD2 VE DENETİM (AUDIT) MANTIĞI:
            'valid_from': ilk_kayit, # Geçerlilik başlangıcı formun doldurulduğu an
            'valid_to': valid_to,
            'is_active': True, # Şu an GETDATE() < valid_to olduğu için aktif
            'islenme_tarihi': islenme_tarihi # Eski data_date yerine ETL'in çalıştığı an
        }
        records_to_append.append(new_record)
        start_no += 1

    df_to_append = pd.DataFrame(records_to_append)

    # data_date yerine islenme_tarihi koyduk
    expected_columns = ['uye_sk', 'uye_no', 'ilk_kayit_tarihi', 'ad', 'soyad', 'email', 'telefon', 
                        'dogum_tarihi', 'yasadigi_sehir', 'uyesi_oldugu_sehir', 'cinsiyet', 
                        'egitim_durumu', 'universite', 'bolum', 'sinif', 'rol', 'notlar', 
                        'valid_from', 'valid_to', 'is_active', 'islenme_tarihi']
    
    for col in expected_columns:
        if col not in df_to_append.columns:
            df_to_append[col] = ""
            
    df_to_append = df_to_append[expected_columns]

    append_data("gencmmg_db", "Dim_Member_History", df_to_append)

    return len(df_to_append), f"{len(df_to_append)} yeni kayıt, yeni SCD2 mantığıyla başarıyla işlendi! 🕰️"

def sp_update_member(uye_no, updated_fields, is_correction=False):
    """
    Üye bilgilerini günceller.
    is_correction=True ise mevcut satırı ezer (Hata Düzeltme).
    is_correction=False ise SCD2 mantığıyla eskiyi kapatır, yeni satır açar.
    """
    from db_utils import get_data, update_row_data, append_data
    import uuid
    from datetime import datetime
    import pandas as pd
    
    df_history = get_data("gencmmg_db", "Dim_Member_History")
    
    # VERİ TİPİ ZIRHI: Hem ID'yi hem de Aktiflik durumunu garantiye alıyoruz
    df_history['is_active_str'] = df_history['is_active'].astype(str).str.strip().str.upper()
    df_history['uye_no_int'] = pd.to_numeric(df_history['uye_no'], errors='coerce').fillna(0).astype(int)
    
    # Aktif kaydı bul
    active_mask = (df_history['uye_no_int'] == int(uye_no)) & (df_history['is_active_str'] == 'TRUE')
    
    if not active_mask.any():
        return False, "Kişinin aktif kaydı bulunamadı."
        
    # Pandas index'ini al (Google Sheets'te hangi satırı güncelleyeceğimizi bulmak için)
    target_index = df_history[active_mask].index[0]
    old_record = df_history.loc[[target_index]].copy()
    
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    expected_columns = ['uye_sk', 'uye_no', 'ilk_kayit_tarihi', 'ad', 'soyad', 'email', 'telefon', 
                        'dogum_tarihi', 'yasadigi_sehir', 'uyesi_oldugu_sehir', 'cinsiyet', 
                        'egitim_durumu', 'universite', 'bolum', 'sinif', 'rol', 'notlar', 
                        'valid_from', 'valid_to', 'is_active', 'islenme_tarihi']

    if is_correction:
        # TİP 1: SEHVEN HATA DÜZELTME (Sadece Değişen Alanları Ez)
        for key, value in updated_fields.items():
            old_record[key] = value
            
        old_record['islenme_tarihi'] = now_str
        old_record = old_record[expected_columns]
        
        # Orijinal satırı üstüne yazarak güncelle
        update_row_data("gencmmg_db", "Dim_Member_History", target_index, old_record)
        return True, "Sehven yapılan hata düzeltildi, tarihçe oluşturulmadı. 🛠️"

    else:
        # TİP 2: SCD2 GÜNCELLEME (Eskiyi Kapat, Yeni Satır Aç)
        
        # 1. Eski Kaydı Kapat (valid_to = Değişme tarihi)
        old_record['valid_to'] = now_str
        old_record['is_active'] = False
        old_record['islenme_tarihi'] = now_str
        old_record = old_record[expected_columns]
        
        update_row_data("gencmmg_db", "Dim_Member_History", target_index, old_record)
        
        # 2. Yeni Satırı Oluştur (valid_from = Bugün, valid_to = 2099)
        new_record = old_record.copy()
        new_record['uye_sk'] = str(uuid.uuid4()) # Yepyeni bir UUID atıyoruz
        
        # Yeni bilgileri bas
        for key, value in updated_fields.items():
            new_record[key] = value
            
        new_record['valid_from'] = now_str
        new_record['valid_to'] = '2099-12-31'
        new_record['is_active'] = True
        new_record['islenme_tarihi'] = now_str
        new_record = new_record[expected_columns]
        
        # Yeni satırı en alta ekle
        append_data("gencmmg_db", "Dim_Member_History", new_record)
        return True, "Yeni bilgiler tarihçe oluşturularak SCD2 formatında kaydedildi! 📝"

def sp_insert_manual_member(form_data):
    """Arayüzden girilen manuel kayıtları veritabanına ekler."""
    from db_utils import get_data, append_data
    import uuid
    from datetime import datetime
    import pandas as pd
    
    df_history = get_data("gencmmg_db", "Dim_Member_History")
    
    # Telefon çoklama kontrolü
    temiz_tel = clean_phone(form_data.get('telefon', ''))
    if not df_history.empty and 'telefon' in df_history.columns:
        existing_phones = df_history['telefon'].astype(str).tolist()
        if temiz_tel in existing_phones and temiz_tel != "":
            return False, "Bu telefon numarası ile sistemde zaten kayıtlı bir kişi var! 🛡️"

    # Yeni Business Key (ID) bul
    start_no = 1001
    if not df_history.empty and 'uye_no' in df_history.columns:
        existing_nos = pd.to_numeric(df_history['uye_no'], errors='coerce').dropna()
        if not existing_nos.empty:
            start_no = int(existing_nos.max()) + 1

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    new_record = {
        'uye_sk': str(uuid.uuid4()),
        'uye_no': start_no,
        'ilk_kayit_tarihi': now_str, # Manuel eklendiği an
        'ad': clean_name(form_data.get('ad', '')),
        'soyad': clean_name(form_data.get('soyad', '')),
        'email': str(form_data.get('email', '')).strip(),
        'telefon': temiz_tel,
        'dogum_tarihi': str(form_data.get('dogum_tarihi', '')).strip(),
        'yasadigi_sehir': clean_city(form_data.get('yasadigi_sehir', '')),
        'uyesi_oldugu_sehir': clean_city(form_data.get('uyesi_oldugu_sehir', '')),
        'cinsiyet': str(form_data.get('cinsiyet', '')).strip(),
        'egitim_durumu': str(form_data.get('egitim_durumu', '')).strip(),
        'universite': clean_school(form_data.get('universite', '')),
        'bolum': clean_school(form_data.get('bolum', '')),
        'sinif': str(form_data.get('sinif', '')).strip(),
        'rol': str(form_data.get('rol', 'Üye')).strip(),
        'notlar': str(form_data.get('notlar', '')).strip(),
        'valid_from': now_str,
        'valid_to': '2099-12-31',
        'is_active': True,
        'islenme_tarihi': now_str
    }
    
    df_to_append = pd.DataFrame([new_record])
    
    expected_columns = ['uye_sk', 'uye_no', 'ilk_kayit_tarihi', 'ad', 'soyad', 'email', 'telefon', 
                        'dogum_tarihi', 'yasadigi_sehir', 'uyesi_oldugu_sehir', 'cinsiyet', 
                        'egitim_durumu', 'universite', 'bolum', 'sinif', 'rol', 'notlar', 
                        'valid_from', 'valid_to', 'is_active', 'islenme_tarihi']
                        
    for col in expected_columns:
        if col not in df_to_append.columns:
            df_to_append[col] = ""
            
    df_to_append = df_to_append[expected_columns]
    
    append_data("gencmmg_db", "Dim_Member_History", df_to_append)
    return True, f"Kişi manuel olarak başarıyla eklendi! Yeni Üye No: {start_no} 🎉"

def sp_deactivate_member(uye_no):
    """Kişiyi pasife alır (Soft Delete). Sadece valid_to ve is_active alanlarını günceller."""
    from db_utils import get_data, update_row_data
    from datetime import datetime
    import pandas as pd
    
    df_history = get_data("gencmmg_db", "Dim_Member_History")
    
    # Veri tiplerini garantiye al
    df_history['is_active_str'] = df_history['is_active'].astype(str).str.strip().str.upper()
    df_history['uye_no_int'] = pd.to_numeric(df_history['uye_no'], errors='coerce').fillna(0).astype(int)
    
    # Aktif kaydı bul
    active_mask = (df_history['uye_no_int'] == int(uye_no)) & (df_history['is_active_str'] == 'TRUE')
    
    if not active_mask.any():
        return False, "Kişinin aktif kaydı bulunamadı."
        
    target_index = df_history[active_mask].index[0]
    old_record = df_history.loc[[target_index]].copy()
    
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    expected_columns = ['uye_sk', 'uye_no', 'ilk_kayit_tarihi', 'ad', 'soyad', 'email', 'telefon', 
                        'dogum_tarihi', 'yasadigi_sehir', 'uyesi_oldugu_sehir', 'cinsiyet', 
                        'egitim_durumu', 'universite', 'bolum', 'sinif', 'rol', 'notlar', 
                        'valid_from', 'valid_to', 'is_active', 'islenme_tarihi']

    # Sadece kapanış tarihlerini ve aktiflik durumunu ez
    old_record['valid_to'] = now_str
    old_record['is_active'] = False
    old_record['islenme_tarihi'] = now_str
    old_record = old_record[expected_columns]
    
    # Satırı güncelle
    update_row_data("gencmmg_db", "Dim_Member_History", target_index, old_record)
    return True, "Kişi başarıyla pasife alındı. Kayıt kapatıldı! 🛑"
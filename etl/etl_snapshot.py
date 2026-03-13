"""Aylık snapshot ETL — Fact_Monthly_Snapshot tablosunu üretir.

SCD2 point-in-time sorgusu:
    valid_from <= reference_dt < valid_to

Referans noktası (reference_dt):
    - Kapanmış ay  → ayın son anı (son gün 23:59:59)
    - Mevcut ay    → şu an (GETDATE eşdeğeri)

Bu koşul, doğru SCD2 verisinde her üye için tam olarak 1 satır döner.
İdempotent: çalışmadan önce ilgili döneme ait satırları siler.
"""

import calendar
from datetime import datetime

import pandas as pd

from constants import (
    SHEET_NAME, HISTORY_WS, SNAPSHOT_WS,
    SNAPSHOT_COLUMNS, SNAPSHOT_MIN_YEAR, SNAPSHOT_MIN_MONTH,
    REPORT_DATETIME_FMT,
)
from utils.db_utils import get_data, append_data, delete_rows_by_value


def snapshot_at_reference(df_history: pd.DataFrame, reference_dt: datetime) -> pd.DataFrame:
    if df_history.empty:
        return df_history.copy()
        
    df = df_history.copy()
    # 'format="mixed"' ekleyerek Pandas'ın satır bazlı format tahmini yapmasını sağlıyoruz
    df['valid_from_dt'] = pd.to_datetime(df['valid_from'], format='mixed', dayfirst=True, errors='coerce')
    df['valid_to_dt'] = pd.to_datetime(df['valid_to'], format='mixed', dayfirst=True, errors='coerce')
    
    # --- DEBUG BLOĞU BAŞLANGICI ---
    # Dönüşemeyen (NaT olan) kayıtları terminale veya arayüze yazdır:
    hatali_kayitlar = df[df['valid_from_dt'].isna() | df['valid_to_dt'].isna()]
    if not hatali_kayitlar.empty:
        print("DIKKAT! Tarihe dönüşemeyen (NaT) satırlar tespit edildi:")
        print(hatali_kayitlar[['uye_no', 'valid_from', 'valid_to']])
    # --- DEBUG BLOĞU BİTİŞİ ---

    return df[
        (df['valid_from_dt'] <= reference_dt) & (df['valid_to_dt'] > reference_dt)
    ].copy()


def _reference_dt_for_period(year: int, month: int) -> datetime:
    """Rapor dönemi için referans tarih: geçmiş ay → ay sonu 23:59:59, mevcut ay → şimdi."""
    last_day = calendar.monthrange(year, month)[1]
    month_end_dt = datetime(year, month, last_day, 23, 59, 59)
    now = datetime.now()
    if (year, month) < (now.year, now.month):
        return month_end_dt
    return now


def preview_monthly_snapshot(
    year: int, month: int, df_history: pd.DataFrame | None = None
) -> tuple[datetime, list[dict]]:
    """
    Dim_Member_History'den Fact'a yazılacak kayıtları üretir; yazmadan döndürür.
    df_history None ise Google Sheets'ten okur; verilirse o DataFrame kullanılır (test/mock).
    Döner: (reference_dt, records) — records, Fact_Monthly_Snapshot'a gidecek satır listesi (dict).
    """
    last_day = calendar.monthrange(year, month)[1]
    month_end_dt = datetime(year, month, last_day, 23, 59, 59)
    rapor_donemi = f"{year}-{month:02d}"
    reference_dt = _reference_dt_for_period(year, month)

    if df_history is None:
        df_history = get_data(SHEET_NAME, HISTORY_WS)
    if df_history.empty:
        return reference_dt, []

    df_snapshot = snapshot_at_reference(df_history, reference_dt)
    if df_snapshot.empty:
        return reference_dt, []

    df_snapshot = df_snapshot.copy()
    df_snapshot['aylik_aktif'] = True
    now_str = datetime.now().strftime(REPORT_DATETIME_FMT)

    records = [
        {
            'data_time':          rapor_donemi,
            'year':               year,
            'month':              month,
            'uye_no':             row['uye_no'],
            'ad':                 row['ad'],
            'soyad':              row['soyad'],
            'email':              row['email'],
            'telefon':            row['telefon'],
            'dogum_tarihi':       row['dogum_tarihi'],
            'yasadigi_sehir':     row['yasadigi_sehir'],
            'uyesi_oldugu_sehir': row['uyesi_oldugu_sehir'],
            'cinsiyet':           row['cinsiyet'],
            'egitim_durumu':      row['egitim_durumu'],
            'universite':         row['universite'],
            'bolum':              row['bolum'],
            'sinif':              row['sinif'],
            'rol':                row['rol'],
            'is_active':          row['aylik_aktif'],
            'islenme_tarihi':     now_str,
            'valid_from':         row['valid_from'],
            'valid_to':           row['valid_to'],
        }
        for _, row in df_snapshot.iterrows()
    ]
    return reference_dt, records


def sp_build_monthly_snapshot(year: int, month: int):
    """
    Döner: (count, mesaj)
    count = 0 ise işlem yapılmamış demektir.
    """
    if (year, month) < (SNAPSHOT_MIN_YEAR, SNAPSHOT_MIN_MONTH):
        return 0, (
            f"En erken izin verilen dönem "
            f"{SNAPSHOT_MIN_YEAR}-{SNAPSHOT_MIN_MONTH:02d}. İşlem iptal."
        )

    rapor_donemi = f"{year}-{month:02d}"
    reference_dt, records = preview_monthly_snapshot(year, month)

    if not records:
        return 0, f"{rapor_donemi} dönemi için aktif kayıt bulunamadı."

    df_out = pd.DataFrame(records)[SNAPSHOT_COLUMNS]
    deleted = delete_rows_by_value(SHEET_NAME, SNAPSHOT_WS, "data_time", rapor_donemi)
    append_data(SHEET_NAME, SNAPSHOT_WS, df_out)

    silindi_notu = f" (önceki {deleted} satır silindi)" if deleted > 0 else ""
    return len(df_out), f"✅ {rapor_donemi} dönemi için {len(df_out)} üye kaydı oluşturuldu{silindi_notu}."

"""Veri temizleme ve dönüştürme yardımcıları.

Saf (pure) fonksiyonlardır; I/O veya yan etki içermez.
"""

import re
import pandas as pd

from constants import START_UYE_NO


def clean_name(text) -> str:
    if pd.isna(text):
        return ""
    return str(text).strip().title()


def clean_phone(text) -> str:
    if pd.isna(text):
        return ""
    num = re.sub(r'\D', '', str(text))
    if num.startswith('0'):
        num = num[1:]
    if num.startswith('90') and len(num) == 12:
        num = num[2:]
    return num


def clean_city(text) -> str:
    if pd.isna(text):
        return ""
    return str(text).title().replace(" ", "")


def clean_school(text) -> str:
    if pd.isna(text):
        return ""
    return str(text).strip().title()


def get_next_uye_no(df_history) -> int:
    """Mevcut Dim_Member_History DataFrame'inden bir sonraki uye_no değerini döner."""
    if df_history.empty or 'uye_no' not in df_history.columns:
        return START_UYE_NO
    existing = pd.to_numeric(df_history['uye_no'], errors='coerce').dropna()
    if existing.empty:
        return START_UYE_NO
    return int(existing.max()) + 1

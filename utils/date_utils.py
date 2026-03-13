"""Ortak tarih parse/format: DD.MM.YYYY HH:MM:SS, dayfirst=True."""

import pandas as pd

from constants import REPORT_DATETIME_FMT


def parse_report_datetime(ser_or_val):
    """
    Rapordaki tarih string'ini (veya Series'i) datetime'a çevirir.
    DD.MM.YYYY veya DD.MM.YYYY HH:MM(:SS) ve karışık formatları kabul eder.
    dayfirst=True kullanır — pandas uyarısı çıkmaz.
    """
    return pd.to_datetime(ser_or_val, errors="coerce", dayfirst=True)


def format_report_datetime(dt):
    """Tekil datetime veya NaT → DD.MM.YYYY HH:MM:SS string."""
    if pd.isna(dt):
        return ""
    if hasattr(dt, "strftime"):
        return dt.strftime(REPORT_DATETIME_FMT)
    return str(dt)

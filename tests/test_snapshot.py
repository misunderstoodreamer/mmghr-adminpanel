"""
Snapshot point-in-time mantığının unit testleri.
Google API kullanılmaz; sadece pandas DataFrame ve snapshot_at_reference fonksiyonu test edilir.

Çalıştırma (proje kökünden):
  python tests/test_snapshot.py

İsteğe bağlı (pytest kuruluysa):
  pytest tests/test_snapshot.py -v
"""

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

# Proje kökü path'e eklensin (tests/ içinden import için)
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from etl.etl_snapshot import snapshot_at_reference
from constants import VALID_TO_OPEN


def _history_row(uye_no: int, valid_from: str, valid_to: str, ad: str = "Test") -> dict:
    """Minimal history satırı (sadece filtrede kullanılan + tanımlayıcı kolonlar)."""
    return {
        "uye_no": uye_no,
        "ad": ad,
        "valid_from": valid_from,
        "valid_to": valid_to,
    }


# --- Referans noktaları (testlerde kullanılacak) ---
REF_2025_06_15 = datetime(2025, 6, 15, 12, 0, 0)
REF_2026_03_13 = datetime(2026, 3, 13, 1, 6, 43)   # uygulamanın yazdığı formata yakın
REF_2025_12_31_END = datetime(2025, 12, 31, 23, 59, 59)
REF_2024_01_01 = datetime(2024, 1, 1, 0, 0, 0)


# --- Test: Rapordaki format (DD.MM.YYYY HH:MM veya HH:MM:SS) ---

def test_yeni_kayit_rapor_formatinda_gelir():
    """Raporda: valid_from=22.12.2025 20:00, valid_to=31.12.2099 00:00:00 → ref 2026-03-13 bu aralıkta, satır seçilmeli."""
    df = pd.DataFrame([
        _history_row(1001, "22.12.2025 20:00", VALID_TO_OPEN, "Ali"),
    ])
    result = snapshot_at_reference(df, REF_2026_03_13)
    assert len(result) == 1
    assert result.iloc[0]["uye_no"] == 1001
    assert result.iloc[0]["ad"] == "Ali"


def test_rapor_format_sadece_saat_dakika():
    """DD.MM.YYYY HH:MM (saniye yok) de parse edilmeli."""
    df = pd.DataFrame([
        _history_row(1002, "01.06.2025 14:30", "31.12.2099 00:00:00", "Veli"),
    ])
    result = snapshot_at_reference(df, REF_2025_06_15)
    assert len(result) == 1
    assert result.iloc[0]["uye_no"] == 1002


def test_gecmis_ay_sonu_referansi():
    """2025 Aralık ayı sonu referans; kayıt 22.12.2025'te başlamış, açık uçlu → seçilmeli."""
    df = pd.DataFrame([
        _history_row(1003, "22.12.2025 20:00", VALID_TO_OPEN, "Ayse"),
    ])
    result = snapshot_at_reference(df, REF_2025_12_31_END)
    assert len(result) == 1
    assert result.iloc[0]["uye_no"] == 1003


# --- Test: referans aralık dışında → satır gelmemeli ---

def test_referans_valid_fromdan_once():
    """reference_dt < valid_from → satır gelmemeli."""
    df = pd.DataFrame([
        _history_row(1004, "01.01.2025 00:00:00", VALID_TO_OPEN, "Dışında"),
    ])
    result = snapshot_at_reference(df, REF_2024_01_01)
    assert len(result) == 0


def test_referans_valid_todan_sonra():
    """reference_dt >= valid_to → satır gelmemeli (kapanmış kayıt)."""
    df = pd.DataFrame([
        _history_row(1005, "01.01.2025 00:00:00", "01.06.2025 00:00:00", "Kapanmış"),
    ])
    result = snapshot_at_reference(df, REF_2025_06_15)
    assert len(result) == 0


def test_referans_valid_to_gununde_ama_saatten_once():
    """reference_dt, valid_to gününde ama saat olarak önce → hâlâ geçerli aralıkta."""
    df = pd.DataFrame([
        _history_row(1006, "01.01.2025 00:00:00", "15.06.2025 18:00:00", "Aralıkta"),
    ])
    result = snapshot_at_reference(df, REF_2025_06_15)
    assert len(result) == 1


# --- Test: Eski uygulama formatı (YYYY-MM-DD HH:MM:SS) ---

def test_eski_uygulama_formati_iso():
    """Eski kayıt: valid_from=2026-03-13 01:06:43, valid_to=2099-12-31 → parse edilip satır seçilmeli."""
    df = pd.DataFrame([
        _history_row(1007, "2026-03-13 01:06:43", "2099-12-31", "EskiFormat"),
    ])
    result = snapshot_at_reference(df, REF_2026_03_13)
    assert len(result) == 1


def test_eski_format_valid_to_sadece_tarih():
    """valid_to '2099-12-31' (saat yok) → gece yarısı 00:00:00 kabul edilir."""
    df = pd.DataFrame([
        _history_row(1008, "01.01.2025 00:00:00", "2099-12-31", "SadeceTarih"),
    ])
    result = snapshot_at_reference(df, REF_2026_03_13)
    assert len(result) == 1


# --- Test: Birden fazla satır (SCD2 versiyonları) ---

def test_scd2_ayni_uye_bir_versiyon_secilir():
    """Aynı uye_no için birden fazla versiyon varsa, reference_dt'e göre sadece biri seçilmeli."""
    df = pd.DataFrame([
        _history_row(1009, "01.01.2025 00:00:00", "01.07.2025 00:00:00", "EskiVersiyon"),
        _history_row(1009, "01.07.2025 00:00:00", VALID_TO_OPEN, "YeniVersiyon"),
    ])
    result = snapshot_at_reference(df, REF_2025_06_15)
    assert len(result) == 1
    assert result.iloc[0]["ad"] == "EskiVersiyon"

    result2 = snapshot_at_reference(df, REF_2026_03_13)
    assert len(result2) == 1
    assert result2.iloc[0]["ad"] == "YeniVersiyon"


# --- Test: Parse hatası (NaT) ---

def test_gecersiz_tarih_satiri_dusmez():
    """valid_from veya valid_to parse edilemezse (NaT) satır filtreden düşer."""
    df = pd.DataFrame([
        _history_row(1010, "32.13.2025 20:00", VALID_TO_OPEN, "Hatali"),
    ])
    result = snapshot_at_reference(df, REF_2026_03_13)
    assert len(result) == 0


def test_bos_dataframe():
    """Boş history → boş snapshot."""
    df = pd.DataFrame(columns=["valid_from", "valid_to", "uye_no", "ad"])
    result = snapshot_at_reference(df, REF_2026_03_13)
    assert len(result) == 0


# --- "Yeni kayıt gelmiyor" senaryosu ---

def test_senaryo_yeni_kayit_ve_eski_kayit_ayni_anda():
    """Yeni kayıt (22.12.2025 20:00 - 31.12.2099) reference 2026-03-13 için mutlaka gelmeli."""
    df = pd.DataFrame([
        _history_row(2001, "22.12.2025 20:00", VALID_TO_OPEN, "YeniKayit"),
        _history_row(2002, "2025-01-01 00:00:00", "2099-12-31", "EskiKayit"),
    ])
    result = snapshot_at_reference(df, REF_2026_03_13)
    assert len(result) >= 1
    assert 2001 in result["uye_no"].tolist(), "Yeni kayıt snapshot'ta olmalı."


# --- Test listesi (pytest olmadan çalıştırmak için) ---

def _run_all():
    tests = [
        test_yeni_kayit_rapor_formatinda_gelir,
        test_rapor_format_sadece_saat_dakika,
        test_gecmis_ay_sonu_referansi,
        test_referans_valid_fromdan_once,
        test_referans_valid_todan_sonra,
        test_referans_valid_to_gununde_ama_saatten_once,
        test_eski_uygulama_formati_iso,
        test_eski_format_valid_to_sadece_tarih,
        test_scd2_ayni_uye_bir_versiyon_secilir,
        test_gecersiz_tarih_satiri_dusmez,
        test_bos_dataframe,
        test_senaryo_yeni_kayit_ve_eski_kayit_ayni_anda,
    ]
    failed = []
    for fn in tests:
        try:
            fn()
            print(f"  OK  {fn.__name__}")
        except Exception as e:
            print(f"  FAIL {fn.__name__}: {e}")
            failed.append((fn.__name__, e))
    if failed:
        print(f"\n{len(failed)} test başarısız.")
        return 1
    print(f"\nTümü geçti ({len(tests)} test).")
    return 0


if __name__ == "__main__":
    print("Snapshot unit testleri (Google API yok)\n")
    sys.exit(_run_all())

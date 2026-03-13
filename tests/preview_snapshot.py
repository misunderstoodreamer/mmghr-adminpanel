"""
Rapor tarihi verirsiniz; Dim_Member_History'den Fact'a yazılacak kayıtlar
yazılmadan pandas listesi (DataFrame) olarak yazdırılır.

Kullanım (proje kökünden):
  python tests/preview_snapshot.py 2026 3
  python tests/preview_snapshot.py 2025 12

Google Sheets'ten Dim_Member_History okunur (credentials gerekir).
Yazma yapılmaz.
"""

import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import pandas as pd
from etl.etl_snapshot import preview_monthly_snapshot


def main():
    if len(sys.argv) < 3:
        print("Kullanım: python tests/preview_snapshot.py YIL AY")
        print("Örnek:    python tests/preview_snapshot.py 2026 3")
        sys.exit(1)

    try:
        year = int(sys.argv[1])
        month = int(sys.argv[2])
    except ValueError:
        print("YIL ve AY sayı olmalı (örn. 2026 3)")
        sys.exit(1)

    if month < 1 or month > 12:
        print("AY 1-12 arası olmalı.")
        sys.exit(1)

    print(f"Rapor dönemi: {year}-{month:02d}")
    print("Dim_Member_History'den okunuyor (Fact'a yazılmıyor)...\n")

    reference_dt, records = preview_monthly_snapshot(year, month, df_history=None)

    print(f"Referans tarih (point-in-time): {reference_dt}")
    print(f"Fact'a gidecek satır sayısı: {len(records)}\n")

    if not records:
        print("Liste boş — bu dönem için valid_from <= ref < valid_to koşulunu sağlayan kayıt yok.")
        return

    df = pd.DataFrame(records)
    csv_path = _root / "snapshot_preview_{}-{:02d}.csv".format(year, month)

    # CSV dosyasına yaz (UTF-8, Excel'de düzgün açılsın diye BOM opsiyonel)
    df.to_csv(csv_path, index=False, encoding="utf-8-sig", sep=";")
    print(f"CSV dosyası: {csv_path}")
    print(f"Satır sayısı: {len(df)} (başlık hariç)\n")

    # Konsola da CSV metnini yazdır (kopyala-yapıştır veya yönlendirme için)
    print(df.to_csv(index=False, encoding="utf-8-sig", sep=";"))


if __name__ == "__main__":
    main()

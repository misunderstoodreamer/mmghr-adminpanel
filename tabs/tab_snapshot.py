import streamlit as st
from datetime import datetime, date
import calendar

from etl.etl_snapshot import sp_build_monthly_snapshot
from constants import SNAPSHOT_MIN_YEAR, SNAPSHOT_MIN_MONTH

# Türkçe ay isimleri
_AYLAR = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]


def _gecerli_donemler() -> list[tuple[int, int]]:
    """Min dönemden bugüne kadar olan tüm (yıl, ay) çiftlerini döner."""
    bugun = date.today()
    donemler = []
    y, m = SNAPSHOT_MIN_YEAR, SNAPSHOT_MIN_MONTH
    while (y, m) <= (bugun.year, bugun.month):
        donemler.append((y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return donemler


def render_snapshot_tab():
    st.subheader("Aylık rapor")
    st.caption(
        "Seçtiğiniz ay için o anki üye listesini rapor tablosuna yazar. "
        "Aynı ay tekrar oluşturulursa o aya ait satırlar güncellenir; diğer aylar değişmez."
    )

    st.markdown(
        """
        **Nasıl çalışır?**  
        Rapor, seçilen ayın sonundaki aktif üyeleri alır. Örneğin Ocak’ta pasife alınan biri, 
        Aralık raporunda yer almaz; Aralık raporunda sadece o ay sonunda hâlâ aktif olanlar görünür.
        """
    )

    st.markdown("---")

    now = datetime.now()

    st.markdown("#### Bu ay")
    bugun_str = f"{_AYLAR[now.month - 1]} {now.year}"
    st.info(f"Mevcut dönem: **{bugun_str}**")

    if st.button("Bu ayın raporunu oluştur / güncelle", type="primary"):
        with st.spinner("Hesaplanıyor…"):
            try:
                count, msg = sp_build_monthly_snapshot(now.year, now.month)
                st.success(msg) if count > 0 else st.warning(msg)
            except Exception as e:
                st.error(f"Hata: {e}")

    st.markdown("---")
    st.markdown("#### Başka bir ay")

    donemler = _gecerli_donemler()
    donem_etiketleri = [
        f"{_AYLAR[m - 1]} {y}" for y, m in reversed(donemler)
    ]
    donem_degerleri = list(reversed(donemler))

    secilen_etiket = st.selectbox(
        "Dönem seçin",
        ["— Seçiniz —"] + donem_etiketleri,
        key="snapshot_donem_select",
    )

    if secilen_etiket != "— Seçiniz —":
        idx = donem_etiketleri.index(secilen_etiket)
        sec_yil, sec_ay = donem_degerleri[idx]
        sec_str = f"{sec_yil}-{sec_ay:02d}"
        sec_label = f"{_AYLAR[sec_ay - 1]} {sec_yil}"

        st.caption(
            f"{sec_label} için mevcut rapor satırları güncellenecek. Diğer aylar değişmez."
        )

        if st.button(f"{sec_label} raporunu oluştur / güncelle"):
            with st.spinner("Hesaplanıyor…"):
                try:
                    count, msg = sp_build_monthly_snapshot(sec_yil, sec_ay)
                    st.success(msg) if count > 0 else st.warning(msg)
                except Exception as e:
                    st.error(f"Hata: {e}")

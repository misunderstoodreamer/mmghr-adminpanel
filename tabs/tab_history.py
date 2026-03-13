import streamlit as st
import pandas as pd

from utils.db_utils import get_data
from constants import SHEET_NAME, HISTORY_WS
from utils.date_utils import parse_report_datetime


def render_history_tab():
    st.subheader("Üye geçmişi")
    st.caption(
        "Bilgisi birden fazla kez güncellenen üyelerin zaman içindeki kayıtları. "
        "Bir üye seçerek tüm değişikliklerini görebilirsiniz."
    )

    df_hist = get_data(SHEET_NAME, HISTORY_WS)

    if df_hist.empty:
        st.info("Henüz kayıt bulunmuyor.")
        return

    df_hist['uye_no_int'] = pd.to_numeric(
        df_hist['uye_no'], errors='coerce'
    ).fillna(0).astype(int)
    df_hist['ilk_kayit_tarihi_dt'] = parse_report_datetime(df_hist['ilk_kayit_tarihi'])

    record_counts = df_hist['uye_no_int'].value_counts()
    multi_users = record_counts[record_counts > 1].index.tolist()

    if not multi_users:
        st.info("Bilgisi güncellenmiş üye yok; geçmiş görüntülemek için önce düzenleme yapılmış olmalı.")
        return

    df_mult = df_hist[df_hist['uye_no_int'].isin(multi_users)].copy()

    first_dates = (
        df_mult.groupby('uye_no_int')['ilk_kayit_tarihi_dt']
        .min()
        .reset_index()
        .sort_values('ilk_kayit_tarihi_dt')
    )

    hist_user_list = []
    for uno in first_dates['uye_no_int']:
        recs = df_mult[df_mult['uye_no_int'] == uno]
        ad       = recs.iloc[-1]['ad']
        soyad    = recs.iloc[-1]['soyad']
        ilk_tarih = recs.iloc[0]['ilk_kayit_tarihi']
        hist_user_list.append(f"{uno} - {ad} {soyad} (İlk Kayıt: {ilk_tarih})")

    selected = st.selectbox(
        "Üye seçin",
        ["Seçiniz…"] + hist_user_list,
    )

    if selected == "Seçiniz…":
        return

    selected_no   = int(selected.split(" - ")[0])
    isim_soyisim  = selected.split(" - ")[1].split(" (")[0]

    user_story = df_hist[df_hist['uye_no_int'] == selected_no].copy()
    user_story = user_story.sort_index(ascending=True)

    display_cols = [
        'ad', 'soyad', 'rol', 'uyesi_oldugu_sehir',
        'yasadigi_sehir', 'valid_from', 'valid_to', 'is_active',
    ]

    st.markdown(f"### {isim_soyisim} — kayıt geçmişi")
    st.dataframe(user_story[display_cols], use_container_width=True, hide_index=True)

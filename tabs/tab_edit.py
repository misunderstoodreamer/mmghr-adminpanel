import streamlit as st
import pandas as pd
from datetime import date

from utils.db_utils import get_data
from constants import SHEET_NAME, HISTORY_WS
from etl.etl_member import sp_update_member, sp_deactivate_member

# Listede gösterilecek kolonlar
_LIST_COLS = ['uye_no', 'ad', 'soyad', 'telefon', 'rol', 'uyesi_oldugu_sehir', 'universite', 'bolum', 'sinif', 'egitim_durumu', 'cinsiyet']


def render_edit_tab():
    st.subheader("Üye bilgisi güncelleme")
    st.caption("Aktif üyeleri listeden seçip bilgilerini güncelleyebilirsiniz.")

    df_history = get_data(SHEET_NAME, HISTORY_WS)

    if df_history.empty or 'is_active' not in df_history.columns:
        st.info("Henüz kayıtlı üye bulunmuyor.")
        return

    df_history['is_active_str'] = (
        df_history['is_active'].astype(str).str.strip().str.upper()
    )
    df_history['uye_no_int'] = pd.to_numeric(
        df_history['uye_no'], errors='coerce'
    ).fillna(0).astype(int)

    df_active = (
        df_history[df_history['is_active_str'] == 'TRUE']
        .sort_values('uye_no_int')
        .reset_index(drop=True)
        .copy()
    )

    if df_active.empty:
        st.warning("Aktif üye bulunamadı.")
        return

    st.caption("Güncellemek istediğiniz kişinin satırına tıklayın.")

    event = st.dataframe(
        df_active[_LIST_COLS],
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )

    if not event.selection.rows:
        return

    sel_i  = event.selection.rows[0]
    row    = df_active.iloc[sel_i]
    uye_no = int(row['uye_no_int'])

    st.markdown("---")
    st.markdown(f"### {row['ad']} {row['soyad']} — Üye no: {row['uye_no']}")

    is_correction = st.checkbox(
        "Sadece yazım hatası / küçük düzeltme (geçmiş kayıt oluşturulmasın)",
        key="edit_is_correction",
    )

    if not is_correction:
        effective_date = st.date_input(
            "Değişiklik hangi tarihten geçerli olsun?",
            value=date.today(),
            max_value=date.today(),
            help="Örneğin değişikliği daha önce yaptıysanız o tarihi seçebilirsiniz. "
                 "Sistem bu tarihe göre geçmiş ve yeni kaydı ayırır.",
            key="edit_effective_date",
        )
        st.caption(f"Seçilen tarih itibarıyla yeni kayıt açılacak; önceki kayıt bu tarihte kapanacak.")
    else:
        effective_date = None
        st.caption("Mevcut kayıt üzerinde güncelleme yapılacak; ek geçmiş satırı oluşturulmayacak.")

    # ── Düzenleme formu ───────────────────────────────────────────────────────
    with st.form("edit_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            f_ad      = st.text_input("Ad",           value=row['ad'])
            f_soyad   = st.text_input("Soyad",        value=row['soyad'])
            f_telefon = st.text_input("Telefon",      value=row['telefon'])
            f_email   = st.text_input("E-Posta",      value=row['email'])
        with c2:
            f_sehir     = st.text_input("Yaşadığı Şehir",     value=row['yasadigi_sehir'])
            f_uye_sehir = st.text_input("Üyesi Olduğu Şehir", value=row['uyesi_oldugu_sehir'])
            f_cinsiyet  = st.text_input("Cinsiyet",           value=row['cinsiyet'])
            f_egitim    = st.text_input("Eğitim Durumu",      value=row['egitim_durumu'])
            f_rol       = st.text_input("Rol",                value=row['rol'])
        with c3:
            f_uni    = st.text_input("Üniversite", value=row['universite'])
            f_bolum  = st.text_input("Bölüm",      value=row['bolum'])
            f_sinif  = st.text_input("Sınıf",      value=row['sinif'])
            f_notlar = st.text_area("Notlar",      value=row['notlar'])

        if st.form_submit_button("Kaydet", type="primary"):
            updated_fields = {
                'ad': f_ad, 'soyad': f_soyad, 'telefon': f_telefon, 'email': f_email,
                'yasadigi_sehir': f_sehir, 'uyesi_oldugu_sehir': f_uye_sehir,
                'cinsiyet': f_cinsiyet, 'egitim_durumu': f_egitim, 'rol': f_rol,
                'universite': f_uni, 'bolum': f_bolum, 'sinif': f_sinif, 'notlar': f_notlar,
            }
            # is_correction ve effective_date form dışında tanımlı —
            # form submit rerun'unda session_state'den okunur
            _is_corr = st.session_state.get("edit_is_correction", False)
            _eff_date = st.session_state.get("edit_effective_date") if not _is_corr else None

            with st.spinner("Kaydediliyor…"):
                success, msg = sp_update_member(
                    uye_no, updated_fields, _is_corr, _eff_date
                )
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("Üyeyi pasife al (artık aktif listede görünmez)"):
        st.warning(
            f"**{row['ad']} {row['soyad']}** pasife alınacak; kayıt kapanacak ve raporlarda aktif olarak sayılmayacak."
        )
        if st.button("Pasife al"):
            with st.spinner("İşleniyor…"):
                success, msg = sp_deactivate_member(uye_no)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

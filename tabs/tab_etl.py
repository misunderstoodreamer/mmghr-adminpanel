import streamlit as st

from etl.etl_member import sp_extract_preview, sp_load_to_history

_PREVIEW_COLS = [
    'ad', 'soyad', 'telefon', 'email', 'dogum_tarihi', 
    'yasadigi_sehir', 'uyesi_oldugu_sehir', 'cinsiyet', 
    'egitim_durumu', 'rol', 'universite', 'bolum', 'sinif', 
    'notlar', 'islenme_tarihi'
]


def render_etl_tab():
    st.subheader("Formdan kayıt aktarma")
    st.caption(
        "Google Form yanıtlarını burada görüntüleyebilir, gerekirse düzenleyip tek seferde sisteme ekleyebilirsiniz."
    )

    if st.button("Yeni form kayıtlarını getir", type="primary"):
        with st.spinner("Form yanıtları kontrol ediliyor…"):
            try:
                df_preview, message = sp_extract_preview()
                if df_preview is not None:
                    st.session_state['etl_preview'] = df_preview
                    st.session_state['etl_msg']     = message
                else:
                    st.session_state.pop('etl_preview', None)
                    st.info(message)
            except Exception as e:
                st.error(f"Hata: {e}")

    # ── ADIM 2: ÖNİZLEME & DÜZENLEME ────────────────────────────────────────
    if st.session_state.get('etl_preview') is None:
        return

    df_prev = st.session_state['etl_preview']

    st.success(st.session_state.get('etl_msg', ''))
    st.markdown("---")

    st.markdown("#### Yeni kayıtlar")
    st.caption("Düzenlemek istediğiniz satıra tıklayın; aşağıda form açılır.")

    event = st.dataframe(
        df_prev[_PREVIEW_COLS].reset_index(drop=True),
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )

    # Seçili satır varsa düzenleme formunu göster
    if event.selection.rows:
        sel_i   = event.selection.rows[0]
        sel_idx = df_prev.index[sel_i]
        row     = df_prev.loc[sel_idx]

        st.markdown(f"#### {row['ad']} {row['soyad']} — düzenleme")

        with st.form("etl_edit_form"):
            c1, c2, c3 = st.columns(3)
            with c1:
                f_ad      = st.text_input("Ad",           value=row['ad'])
                f_soyad   = st.text_input("Soyad",        value=row['soyad'])
                f_email   = st.text_input("E-Posta",      value=row['email'])
                f_telefon = st.text_input("Telefon",      value=row['telefon'])
                f_dogum   = st.text_input("Doğum Tarihi", value=row['dogum_tarihi'])
            with c2:
                f_yasadigi = st.text_input("Yaşadığı Şehir",     value=row['yasadigi_sehir'])
                f_uyesi    = st.text_input("Üyesi Olduğu Şehir", value=row['uyesi_oldugu_sehir'])
                f_cinsiyet = st.text_input("Cinsiyet",           value=row['cinsiyet'])
                f_egitim   = st.text_input("Eğitim Durumu",      value=row['egitim_durumu'])
                f_rol      = st.text_input("Rol",                value=row['rol'])
            with c3:
                f_uni    = st.text_input("Üniversite", value=row['universite'])
                f_bolum  = st.text_input("Bölüm",      value=row['bolum'])
                f_sinif  = st.text_input("Sınıf",      value=row['sinif'])
                f_notlar = st.text_area("Notlar",      value=row['notlar'])

            if st.form_submit_button("Değişiklikleri uygula"):
                updates = {
                    'ad': f_ad, 'soyad': f_soyad, 'email': f_email,
                    'telefon': f_telefon, 'dogum_tarihi': f_dogum,
                    'yasadigi_sehir': f_yasadigi, 'uyesi_oldugu_sehir': f_uyesi,
                    'cinsiyet': f_cinsiyet, 'egitim_durumu': f_egitim,
                    'universite': f_uni, 'bolum': f_bolum,
                    'sinif': f_sinif, 'rol': f_rol, 'notlar': f_notlar,
                }
                for field, val in updates.items():
                    st.session_state['etl_preview'].at[sel_idx, field] = val
                st.success(f"{f_ad} {f_soyad} için değişiklikler kaydedildi.")
                st.rerun()

    st.markdown("---")
    col_load, col_cancel = st.columns(2)
    with col_load:
        if st.button("Tümünü sisteme kaydet", type="primary"):
            with st.spinner("Kayıtlar ekleniyor…"):
                try:
                    count, msg = sp_load_to_history(
                        st.session_state['etl_preview'].copy()
                    )
                    st.success(msg)
                    st.session_state.pop('etl_preview', None)
                    st.session_state.pop('etl_msg', None)
                    st.rerun()
                except Exception as e:
                    st.error(f"Hata: {e}")
    with col_cancel:
        if st.button("İptal et"):
            st.session_state.pop('etl_preview', None)
            st.session_state.pop('etl_msg', None)
            st.rerun()

import streamlit as st

from etl.etl_member import sp_insert_manual_member


def render_manual_tab():
    st.subheader("Form kullanmadan üye ekleme")
    st.caption("Form doldurmayan kişileri doğrudan buradan sisteme ekleyebilirsiniz.")

    with st.form("manual_insert_form", clear_on_submit=True):
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            m_ad      = st.text_input("Ad", placeholder="Zorunlu")
            m_soyad   = st.text_input("Soyad", placeholder="Zorunlu")
            m_email   = st.text_input("E-posta")
            m_telefon = st.text_input("Telefon", placeholder="Zorunlu")
            m_dogum   = st.text_input("Doğum tarihi")
        with col_m2:
            m_yasadigi_sehir = st.text_input("Yaşadığı şehir")
            m_uyesi_sehir    = st.text_input("Üyesi olduğu şehir")
            m_cinsiyet = st.selectbox(
                "Cinsiyet", ["Seçiniz", "Kadın", "Erkek", "Belirtmek istemiyorum"]
            )
            m_egitim = st.selectbox(
                "Eğitim durumu",
                ["Seçiniz", "Lisans", "Yüksek Lisans", "Doktora", "Mezun", "Diğer"],
            )
            m_rol = st.text_input("Rol", value="Üye")
        with col_m3:
            m_uni    = st.text_input("Üniversite")
            m_bolum  = st.text_input("Bölüm")
            m_sinif  = st.text_input("Sınıf")
            m_notlar = st.text_area("Notlar")

        submitted = st.form_submit_button("Kaydet")
        if submitted:
            if not m_ad or not m_soyad or not m_telefon:
                st.error("Ad, soyad ve telefon alanları zorunludur.")
            else:
                form_data = {
                    'ad': m_ad, 'soyad': m_soyad, 'email': m_email,
                    'telefon': m_telefon, 'dogum_tarihi': m_dogum,
                    'yasadigi_sehir': m_yasadigi_sehir,
                    'uyesi_oldugu_sehir': m_uyesi_sehir,
                    'cinsiyet':      "" if m_cinsiyet == "Seçiniz" else m_cinsiyet,
                    'egitim_durumu': "" if m_egitim   == "Seçiniz" else m_egitim,
                    'universite': m_uni, 'bolum': m_bolum, 'sinif': m_sinif,
                    'rol': m_rol, 'notlar': m_notlar,
                }
                with st.spinner("Kayıt ekleniyor…"):
                    success, msg = sp_insert_manual_member(form_data)
                    if success:
                        st.success(msg)
                    else:
                        st.error(msg)

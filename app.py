import streamlit as st
import pandas as pd
from db_utils import get_data
from etl_procs import sp_staging_to_history, sp_update_member, sp_insert_manual_member, sp_deactivate_member

# Sayfa ayarı her zaman en üstte, şifreden bile önce olmalıdır!
st.set_page_config(page_title="Genç MMG İK Admin", page_icon="⚙️", layout="wide")

# ==========================================
# GÜVENLİK (LOGIN) KATMANI
# ==========================================
def check_password():
    """Kullanıcı doğru şifreyi girdiyse True döner ve sayfayı açar."""
    def password_entered():
        # ŞİFRENİ BURADAN DEĞİŞTİREBİLİRSİN:
        if st.session_state["password"] == "mmg1996":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Güvenlik için şifreyi hafızadan sil
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # İlk açılış: Sadece şifre kutusunu göster
        st.title("🔒 Genç MMG İK Paneline Giriş")
        st.text_input("Lütfen Admin Şifrenizi Girin", type="password", on_change=password_entered, key="password")
        return False
        
    elif not st.session_state["password_correct"]:
        # Yanlış şifre durumu
        st.title("🔒 Genç MMG İK Paneline Giriş")
        st.text_input("Lütfen Admin Şifrenizi Girin", type="password", on_change=password_entered, key="password")
        st.error("😕 Hatalı şifre. Lütfen tekrar deneyin.")
        return False
        
    else:
        # Şifre doğru, içeri geçebilir
        return True


# ==========================================
# ANA UYGULAMA (SADECE ŞİFRE DOĞRUYSA ÇALIŞIR)
# ==========================================
if check_password():
    
    st.title("👥 Genç MMG Üye Veri Yönetimi Admin Paneli")

    # --- 4 SEKME (TABS) OLUŞTURUYORUZ ---
    tab_etl, tab_manual, tab_edit, tab_history = st.tabs([
        "🚀 Formdan Çek (ETL)", 
        "➕ Manuel Kayıt", 
        "✏️ Kişi Düzenleme", 
        "📜 Kişinin Hikayesi"
    ])

    # ==========================================
    # SEKME 1: YENİ KAYITLARI ÇEK
    # ==========================================
    with tab_etl:
        st.subheader("Veri Ambarını Besle (Google Form)")
        st.write("Google Form'dan gelen ham yanıtları ana veritabanına aktarır.")
        
        if st.button("🚀 Yeni Form Kayıtlarını Çek", type="primary"):
            with st.spinner("Veriler işleniyor..."):
                try:
                    count, message = sp_staging_to_history()
                    if count > 0:
                        st.success(message)
                    else:
                        st.info(message)
                except Exception as e:
                    st.error(f"Bir hata oluştu: {e}")

    # ==========================================
    # SEKME 2: MANUEL KAYIT
    # ==========================================
    with tab_manual:
        st.subheader("Sisteme Manuel Üye Ekle")
        st.write("Form doldurmayan kişileri doğrudan veritabanına SCD2 standartlarında ekleyin.")
        
        with st.form("manual_insert_form", clear_on_submit=True):
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                m_ad = st.text_input("Ad *")
                m_soyad = st.text_input("Soyad *")
                m_email = st.text_input("E-Posta Adresi")
                m_telefon = st.text_input("Telefon *")
                m_dogum = st.text_input("Doğum Tarihi")
            with col_m2:
                m_yasadigi_sehir = st.text_input("Yaşadığı Şehir")
                m_uyesi_sehir = st.text_input("Üyesi Olduğu Şehir")
                m_cinsiyet = st.selectbox("Cinsiyet", ["Seçiniz", "Kadın", "Erkek", "Belirtmek İstemiyorum"])
                m_egitim = st.selectbox("Eğitim Durumu", ["Seçiniz", "Lisans", "Yüksek Lisans", "Doktora", "Mezun", "Diğer"])
                m_rol = st.text_input("Kurum İçi Rolü", value="Üye")
            with col_m3:
                m_uni = st.text_input("Üniversite")
                m_bolum = st.text_input("Bölüm")
                m_sinif = st.text_input("Sınıf")
                m_notlar = st.text_area("Notlar")
                
            submitted = st.form_submit_button("➕ Sisteme Kaydet")
            if submitted:
                if not m_ad or not m_soyad or not m_telefon:
                    st.error("Ad, Soyad ve Telefon alanları zorunludur!")
                else:
                    form_data = {
                        'ad': m_ad, 'soyad': m_soyad, 'email': m_email, 'telefon': m_telefon,
                        'dogum_tarihi': m_dogum, 'yasadigi_sehir': m_yasadigi_sehir, 
                        'uyesi_oldugu_sehir': m_uyesi_sehir, 
                        'cinsiyet': "" if m_cinsiyet == "Seçiniz" else m_cinsiyet,
                        'egitim_durumu': "" if m_egitim == "Seçiniz" else m_egitim,
                        'universite': m_uni, 'bolum': m_bolum, 'sinif': m_sinif,
                        'rol': m_rol, 'notlar': m_notlar
                    }
                    with st.spinner("Kayıt veritabanına işleniyor..."):
                        success, msg = sp_insert_manual_member(form_data)
                        if success: st.success(msg)
                        else: st.error(msg)

    # ==========================================
    # SEKME 3: KİŞİ DÜZENLEME & DEAKTİVASYON
    # ==========================================
    with tab_edit:
        st.subheader("Üye Bilgisi ve Görev Güncelleme")
        df_history = get_data("gencmmg_db", "Dim_Member_History")
        
        if not df_history.empty and 'is_active' in df_history.columns:
            df_history['is_active_str'] = df_history['is_active'].astype(str).str.strip().str.upper()
            df_history['uye_no_int'] = pd.to_numeric(df_history['uye_no'], errors='coerce').fillna(0).astype(int)
            
            df_active = df_history[df_history['is_active_str'] == 'TRUE'].copy()
            
            if df_active.empty:
                st.warning("Veritabanında 'Aktif' durumda olan hiç kimse bulunamadı.")
            else:
                user_list = df_active.apply(lambda x: f"{x['uye_no']} - {x['ad']} {x['soyad']} ({x['rol']})", axis=1).tolist()
                selected_user = st.selectbox("🔍 Düzenlenecek Kişiyi Seçin:", ["Seçiniz..."] + sorted(user_list))
                
                if selected_user != "Seçiniz...":
                    selected_no = int(selected_user.split(" - ")[0])
                    user_data = df_active[df_active['uye_no_int'] == selected_no].iloc[0]
                    
                    st.markdown("---")
                    col1, col2 = st.columns(2)
                    with col1:
                        new_ad = st.text_input("Ad", user_data['ad'])
                        new_soyad = st.text_input("Soyad", user_data['soyad'])
                        new_telefon = st.text_input("Telefon", user_data['telefon'])
                        new_sehir = st.text_input("Yaşadığı Şehir", user_data['yasadigi_sehir'])
                        new_uye_sehir = st.text_input("Üyesi Olduğu Şehir", user_data.get('uyesi_oldugu_sehir', ''))
                    with col2:
                        new_rol = st.text_input("Kurum İçi Rolü / Görevi", user_data['rol'])
                        new_uni = st.text_input("Üniversite", user_data['universite'])
                        new_bolum = st.text_input("Bölüm", user_data['bolum'])
                        new_sinif = st.text_input("Sınıf", user_data['sinif'])
                        
                    st.markdown("---")
                    is_correction = st.checkbox("⚠️ Bu bir 'Sehven Hata Düzeltme' işlemidir. (Tarihçe açılmaz)")
                    
                    if st.button("💾 Değişiklikleri Kaydet", type="primary"):
                        updated_fields = {
                            'ad': new_ad, 'soyad': new_soyad, 'telefon': new_telefon,
                            'yasadigi_sehir': new_sehir, 'uyesi_oldugu_sehir': new_uye_sehir, 
                            'rol': new_rol, 'universite': new_uni, 'bolum': new_bolum, 'sinif': new_sinif
                        }
                        with st.spinner("Veritabanı güncelleniyor..."):
                            success, msg = sp_update_member(selected_no, updated_fields, is_correction)
                            if success:
                                st.success(msg)
                                st.rerun()
                            else: st.error(msg)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    with st.expander("🛑 Tehlikeli Alan: Üyeyi Pasife Al (Deaktive Et)"):
                        st.warning("Bu işlem kişiyi tamamen pasife alır. 'valid_to' tarihi şu anki saniyeye eşitlenir.")
                        if st.button("🚨 Evet, Kişiyi Pasife Al ve Kapat"):
                            with st.spinner("Kayıt kapatılıyor..."):
                                success, msg = sp_deactivate_member(selected_no)
                                if success:
                                    st.success(msg)
                                    st.rerun()
                                else: st.error(msg)
        else:
            st.info("Veritabanında kayıt bulunamadı.")

    # ==========================================
    # SEKME 4: KİŞİNİN HİKAYESİ (SCD2 LOGLARI)
    # ==========================================
    with tab_history:
        st.subheader("📜 Üye Değişim Tarihçesi")
        st.write("Aşağıda sadece sistemde **birden fazla kaydı bulunan** üyeler, **ilk kayıt tarihlerine** göre eskiden yeniye sıralanmıştır.")
        
        df_hist_tab = get_data("gencmmg_db", "Dim_Member_History")
        
        if not df_hist_tab.empty:
            df_hist_tab['uye_no_int'] = pd.to_numeric(df_hist_tab['uye_no'], errors='coerce').fillna(0).astype(int)
            df_hist_tab['ilk_kayit_tarihi_dt'] = pd.to_datetime(df_hist_tab['ilk_kayit_tarihi'], errors='coerce')
            
            # SADECE BİRDEN FAZLA KAYDI OLANLARI BUL
            record_counts = df_hist_tab['uye_no_int'].value_counts()
            multiple_record_users = record_counts[record_counts > 1].index.tolist()
            
            if not multiple_record_users:
                st.info("Henüz sistemde bir güncelleme/değişiklik yaşamış üye bulunmuyor.")
            else:
                # Birden fazla kaydı olanları filtrele
                df_mult = df_hist_tab[df_hist_tab['uye_no_int'].isin(multiple_record_users)].copy()
                
                # Üyeleri İLK KAYIT TARİHİNE GÖRE sıralamak için en eski tarihlerini bul
                first_dates = df_mult.groupby('uye_no_int')['ilk_kayit_tarihi_dt'].min().reset_index()
                first_dates = first_dates.sort_values(by='ilk_kayit_tarihi_dt', ascending=True)
                
                hist_user_list = []
                for uno in first_dates['uye_no_int']:
                    user_records = df_mult[df_mult['uye_no_int'] == uno]
                    ad = user_records.iloc[-1]['ad']
                    soyad = user_records.iloc[-1]['soyad']
                    ilk_tarih = user_records.iloc[0]['ilk_kayit_tarihi']
                    hist_user_list.append(f"{uno} - {ad} {soyad} (İlk Kayıt: {ilk_tarih})")
                    
                selected_hist_user = st.selectbox("🔍 Hikayesini Görmek İstediğiniz Üyeyi Seçin:", ["Seçiniz..."] + hist_user_list)
                
                if selected_hist_user != "Seçiniz...":
                    selected_no_hist = int(selected_hist_user.split(" - ")[0])
                    isim_soyisim = selected_hist_user.split(" - ")[1].split(" (")[0]
                    
                    # Fiziksel sıraya (index) göre diz, tarih formatı hatasından kurtul!
                    user_story_df = df_hist_tab[df_hist_tab['uye_no_int'] == selected_no_hist].copy()
                    user_story_df = user_story_df.sort_index(ascending=True)
                    
                    display_cols = ['ad', 'soyad', 'rol', 'uyesi_oldugu_sehir', 'yasadigi_sehir', 'valid_from', 'valid_to', 'is_active']
                    
                    st.markdown(f"### 🚀 {isim_soyisim} - Kariyer Çizgisi")
                    st.dataframe(user_story_df[display_cols], use_container_width=True, hide_index=True)
        else:
            st.info("Veritabanı şu an boş.")
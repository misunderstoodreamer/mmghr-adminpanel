import streamlit as st

from theme import inject_theme
from tabs.tab_etl      import render_etl_tab
from tabs.tab_manual   import render_manual_tab
from tabs.tab_edit     import render_edit_tab
from tabs.tab_history  import render_history_tab
from tabs.tab_snapshot import render_snapshot_tab

st.set_page_config(
    page_title="Genç MMG Üye Yönetimi",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_theme()


def check_password() -> bool:
    if st.session_state.get("password_correct"):
        return True

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### Giriş")
    st.markdown("Yönetim paneline erişmek için şifrenizi girin.")
    with st.form("login_form"):
        password = st.text_input("Şifre", type="password", label_visibility="collapsed", placeholder="Şifrenizi yazın…")
        submitted = st.form_submit_button("Giriş yap")
    if submitted:
        if password == st.secrets["admin_password"]:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Şifre hatalı. Lütfen tekrar deneyin.")
    return False


if check_password():
    st.title("Genç MMG Üye Yönetim Paneli")
    st.caption("Üye kayıtları, güncellemeler ve aylık raporlar buradan yönetilir.")

    tab_etl, tab_manual, tab_edit, tab_history, tab_snapshot = st.tabs([
        "Formdan aktar",
        "Üye ekle",
        "Bilgi güncelle",
        "Üye geçmişi",
        "Aylık rapor",
    ])

    with tab_etl:      render_etl_tab()
    with tab_manual:   render_manual_tab()
    with tab_edit:     render_edit_tab()
    with tab_history:  render_history_tab()
    with tab_snapshot: render_snapshot_tab()

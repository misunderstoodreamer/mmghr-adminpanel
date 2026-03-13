"""
Uygulama genelinde kullanılan tema (CSS).
Streamlit ile st.markdown(..., unsafe_allow_html=True) ile enjekte edilir.
"""

MAIN_CSS = """
<style>
  /* Koyu, göz yormayan arka plan (soft dark) */
  .stApp {
    background: linear-gradient(180deg, #2d3748 0%, #1a202c 100%);
  }
  /* Başlıklar — açık metin */
  h1, h2, h3 {
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    font-weight: 600;
    color: #e2e8f0;
    letter-spacing: -0.02em;
  }
  h1 { font-size: 1.75rem; margin-bottom: 0.5rem; }
  h2 { font-size: 1.35rem; margin-top: 1.25rem; margin-bottom: 0.5rem; }
  h3 { font-size: 1.15rem; margin-top: 1rem; }
  /* Paragraf ve açıklamalar */
  p, .stMarkdown {
    color: #cbd5e1;
    line-height: 1.55;
  }
  [data-testid="stCaptionContainer"] {
    color: #94a3b8;
  }
  /* Sekmeler */
  .stTabs [data-baseweb="tab-list"] {
    gap: 0.25rem;
    background: rgba(45, 55, 72, 0.8);
    padding: 0.5rem;
    border-radius: 10px;
    border: 1px solid rgba(255,255,255,0.08);
  }
  .stTabs [data-baseweb="tab"] {
    padding: 0.6rem 1rem;
    border-radius: 8px;
    font-weight: 500;
    color: #94a3b8;
  }
  .stTabs [aria-selected="true"] {
    background: #4a5568;
    color: #f7fafc;
  }
  /* Streamlit widget metinleri okunaklı kalsın */
  [data-testid="stWidgetLabel"] p, label {
    color: #cbd5e1 !important;
  }
  /* Bilgi / uyarı kutuları */
  [data-testid="stAlert"] {
    border-radius: 10px;
    border-left-width: 4px;
  }
  /* Buton */
  .stButton > button {
    border-radius: 8px;
    font-weight: 500;
    transition: box-shadow 0.2s ease;
  }
  .stButton > button:hover {
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
  }
  /* Genel boşluk */
  .block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1200px;
  }

  /* ----- Form ve tablo alanları: açık / hafif gri ----- */
  /* Form kapsayıcısı — hafif gri */
  [data-testid="stForm"] {
    background: #e3e3e3;
    padding: 1.25rem 1.5rem;
    border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }
  /* Metin kutusu, input, select, textarea — hafif gri (beyaz değil) */
  .stTextInput input, .stNumberInput input,
  .stTextArea textarea,
  [data-baseweb="select"] > div,
  [data-baseweb="input"] {
    background-color: #f8fafc !important;
    color: #1e293b !important;
    border-color: #e2e8f0 !important;
  }
  [data-baseweb="calendar"] {
    background: #f8fafc !important;
  }
  /* Form içi label'lar açık kutuda koyu yazı */
  [data-testid="stForm"] [data-testid="stWidgetLabel"] p,
  [data-testid="stForm"] label {
    color: #334155 !important;
  }

  /* ----- Tablo: açık arka plan, koyu metin (veriler siyah kalmasın) ----- */
  [data-testid="stDataFrame"],
  div[data-testid="stDataFrameResizable"] {
    background: #f8fafc !important;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }
  /* Tablo — tüm içerik açık zemin, koyu yazı */
  [data-testid="stDataFrame"] table,
  [data-testid="stDataFrameResizable"] table,
  .stDataFrame table {
    background: #f8fafc !important;
    color: #1e293b !important;
  }
  [data-testid="stDataFrame"] thead th,
  [data-testid="stDataFrameResizable"] thead th,
  .stDataFrame thead th {
    background: #e2e8f0 !important;
    color: #1e293b !important;
    border-bottom: 1px solid #cbd5e1 !important;
  }
  [data-testid="stDataFrame"] tbody tr:nth-child(odd),
  [data-testid="stDataFrameResizable"] tbody tr:nth-child(odd),
  .stDataFrame tbody tr:nth-child(odd) {
    background: #f1f5f9 !important;
  }
  [data-testid="stDataFrame"] tbody tr:nth-child(even),
  [data-testid="stDataFrameResizable"] tbody tr:nth-child(even),
  .stDataFrame tbody tr:nth-child(even) {
    background: #f8fafc !important;
  }
  [data-testid="stDataFrame"] tbody td,
  [data-testid="stDataFrameResizable"] tbody td,
  .stDataFrame tbody td {
    background: inherit !important;
    color: #1e293b !important;
    border-color: #e2e8f0 !important;
  }
  /* Hücre içi span/div — metin rengi koyu */
  [data-testid="stDataFrame"] td span, [data-testid="stDataFrame"] td div,
  [data-testid="stDataFrameResizable"] td span, [data-testid="stDataFrameResizable"] td div,
  .stDataFrame td span, .stDataFrame td div {
    color: #1e293b !important;
  }
  /* Glide / role="row" + role="cell" — açık zemin, koyu yazı */
  [data-testid="stDataFrame"] [role="row"]:nth-of-type(odd) {
    background: #f1f5f9 !important;
  }
  [data-testid="stDataFrame"] [role="row"]:nth-of-type(even) {
    background: #f8fafc !important;
  }
  [data-testid="stDataFrame"] [role="cell"],
  [data-testid="stDataFrameResizable"] [role="cell"] {
    background: inherit !important;
    color: #1e293b !important;
  }
  [data-testid="stDataFrame"] [role="cell"] span,
  [data-testid="stDataFrame"] [role="cell"] div,
  [data-testid="stDataFrameResizable"] [role="cell"] span,
  [data-testid="stDataFrameResizable"] [role="cell"] div {
    color: #1e293b !important;
  }

  /* Expander — hafif gri kutu */
  [data-testid="stExpander"] {
    background: #f1f5f9;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
  }
  [data-testid="stExpander"] details {
    background: #f1f5f9 !important;
  }
  [data-testid="stExpander"] [data-testid="stMarkdown"] {
    color: #334155 !important;
  }
</style>
"""


def inject_theme():
    """Tema CSS'ini sayfaya enjekte eder. app.py içinde bir kez çağrılmalı."""
    import streamlit as st
    st.markdown(MAIN_CSS, unsafe_allow_html=True)

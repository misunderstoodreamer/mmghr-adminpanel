import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_client():
    # 1. BULUT KONTROLÜ (Streamlit Cloud Secrets)
    if "gcp_service_account" in st.secrets:
        # st.secrets'ı dict'e çevirip JSON gibi okutuyoruz
        creds_dict = dict(st.secrets["gcp_service_account"])
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
    
    # 2. LOKAL KONTROL (Kendi bilgisayarımız)
    else:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", SCOPE)
        
    return gspread.authorize(creds)

def get_data(sheet_name, worksheet_name):
    """Belirtilen tablodan veriyi okur ve Pandas DataFrame olarak döner."""
    client = get_client()
    sheet = client.open(sheet_name).worksheet(worksheet_name)
    records = sheet.get_all_records()
    return pd.DataFrame(records)

def append_data(sheet_name, worksheet_name, df):
    """DataFrame'i belirtilen tablonun en altına ekler."""
    client = get_client()
    sheet = client.open(sheet_name).worksheet(worksheet_name)
    # NaN değerleri Google Sheets JSON formatında hata vermesin diye boş string yapıyoruz
    df = df.fillna("") 
    sheet.append_rows(df.values.tolist())

def delete_rows_by_value(sheet_name, worksheet_name, column_name, value):
    """Belirtilen kolonda value ile eşleşen tüm satırları siler. Silinen satır sayısını döner."""
    client = get_client()
    sheet = client.open(sheet_name).worksheet(worksheet_name)

    all_values = sheet.get_all_values()
    if not all_values:
        return 0

    headers = all_values[0]
    if column_name not in headers:
        return 0

    col_idx = headers.index(column_name)

    # Silinecek satır numaralarını topla (1-indexed; 1. satır başlık)
    rows_to_delete = [
        i + 2  # +2: satır 1 başlık, enumerate 0'dan başlıyor
        for i, row in enumerate(all_values[1:])
        if len(row) > col_idx and row[col_idx] == str(value)
    ]

    # Tersten silerek index kaymasını önle
    for row_num in sorted(rows_to_delete, reverse=True):
        sheet.delete_rows(row_num)

    return len(rows_to_delete)


def update_row_data(sheet_name, worksheet_name, row_index, df_row):
    """Belirtilen satırdaki veriyi Google Sheets üzerinde günceller."""
    client = get_client()
    sheet = client.open(sheet_name).worksheet(worksheet_name)
    
    # NaN değerleri temizle
    df_row = df_row.fillna("")
    
    # gspread satır indeksi 1'den başlar. 
    # Pandas 0'dan başlar, 1 tane de başlık (Header) satırı var.
    # Yani Pandas Index 0 = Google Sheets Row 2
    gsheets_row = row_index + 2 
    
    values = df_row.values.tolist()[0] # Tek satırlık listeyi al
    
    # A'dan U'ya kadar olan hücreleri güncelle (21 Kolon)
    # Gspread versiyon uyumluluğu için range formatı:
    cell_range = f'A{gsheets_row}:U{gsheets_row}'
    sheet.update(values=[values], range_name=cell_range)

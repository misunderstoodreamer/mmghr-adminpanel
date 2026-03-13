# Uygulama genelinde paylaşılan sabitler.
# Hiçbir iş mantığı bu dosyada bulunmaz.

SHEET_NAME = "gencmmg_db"
HISTORY_WS = "Dim_Member_History"
STAGING_WS = "Staging_Form"
SNAPSHOT_WS = "Fact_Monthly_Snapshot"

# Tüm uygulama: tarih formatı DD.MM.YYYY HH:MM:SS (gün.ay.yıl saat:dakika:saniye)
# Parse ederken her yerde dayfirst=True kullanın (pandas uyarısını önler).
REPORT_DATETIME_FMT = "%d.%m.%Y %H:%M:%S"
VALID_TO_OPEN = "31.12.2099 00:00:00"
START_UYE_NO = 1001

SNAPSHOT_MIN_YEAR = 2025
SNAPSHOT_MIN_MONTH = 12

HISTORY_COLUMNS = [
    'uye_sk', 'uye_no', 'ilk_kayit_tarihi', 'ad', 'soyad', 'email',
    'telefon', 'dogum_tarihi', 'yasadigi_sehir', 'uyesi_oldugu_sehir',
    'cinsiyet', 'egitim_durumu', 'universite', 'bolum', 'sinif',
    'rol', 'notlar', 'valid_from', 'valid_to', 'is_active', 'islenme_tarihi'
]

SNAPSHOT_COLUMNS = [
    'data_time', 'year', 'month', 'uye_no',
    'ad', 'soyad', 'email', 'telefon', 'dogum_tarihi',
    'yasadigi_sehir', 'uyesi_oldugu_sehir', 'cinsiyet', 'egitim_durumu',
    'universite', 'bolum', 'sinif', 'rol',
    'is_active', 'islenme_tarihi', 'valid_from', 'valid_to'
]

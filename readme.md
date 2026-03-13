# Genç MMG İK Veri Yönetimi ve Admin Paneli

Bu proje, Genç MMG topluluğunun üye verilerini ve görev tarihçesini yönetmek için
hazırlanmış, Google Sheets’i veri ambarı olarak kullanan bir **Streamlit** uygulamasıdır.

- Google Forms yanıtlarını otomatik çekip temizler.
- Üye bilgilerini SCD Type 1 ve Type 2 mantığıyla tarihçeli tutar.
- Manuel üye ekleme, bilgi güncelleme ve pasife alma (soft delete) sunar.
- Aylık snapshot (Fact_Monthly_Snapshot) üreterek Looker Studio vb. raporlara kaynak olur.

Tüm tarih alanları uygulama genelinde **`DD.MM.YYYY HH:MM:SS`** formatında tutulur
ve `dayfirst=True` ile parse edilir.

---

## Temel Özellikler

- **Formdan otomatik ETL**
  - Google Forms → `Staging_Form` → temizlik / dedup → `Dim_Member_History`
  - Zaman damgasına göre sıralı, telefon bazlı tekrar kontrolü, aynı üye için tek kayıt.

- **SCD Type 1 & Type 2 güncelleme**
  - Küçük/yazım hataları için **SCD1** (mevcut satır üzerinde düzeltme).
  - Görev, şehir, rol vb. değişiklikler için **SCD2**:
    - Eski kayıt `valid_to` ile kapanır.
    - Yeni kayıt `valid_from` ile açılır; `valid_to = 31.12.2099 00:00:00`.

- **Manuel üye ekleme**
  - Form doldurmayan kişileri arayüzden, aynı veri standartlarıyla ekleme.

- **Soft delete (deaktivasyon)**
  - Üye fiziksel olarak silinmez, `is_active = False` ve `valid_to = now` yapılır.
  - Geçmiş dönem raporları bozulmaz.

- **Üye geçmişi**
  - Bir üyenin tüm versiyonlarını (görev/departman/şehir değişimleri) kronolojik listeler.

- **Aylık snapshot (Fact_Monthly_Snapshot)**
  - `valid_from <= reference_dt < valid_to` kuralı ile ay sonu itibarıyla aktif kaydı seçer.
  - Her ay için tek bir “durum fotoğrafı” üretir; aynı ay tekrar çalıştırılırsa o aya ait
    satırlar silinip yeniden yazılır.

- **Güvenlik katmanı**
  - `admin_password` ile basit ama yeterli admin girişi (`.streamlit/secrets.toml`).

---

## Teknoloji Yığını

- **Arayüz ve uygulama mantığı**: Streamlit (Python)
- **Veri ambarı / veritabanı**: Google Sheets
- **API istemcisi**: `gspread`, `oauth2client`
- **Veri dönüşümleri**: `pandas`

---

## Proje Klasör Yapısı

```text
.
├── app.py                 # Ana Streamlit uygulaması (sekme orkestratörü)
├── theme.py               # Uygulama genel CSS teması (koyu tema + açık formlar/tablolar)
├── constants.py           # Google Sheets isimleri, kolon listeleri, tarih formatı vb.
├── utils/
│   ├── __init__.py
│   ├── db_utils.py        # Google Sheets okuma/yazma (get_data, append_data, update_row_data, delete_rows_by_value)
│   ├── date_utils.py      # Tarih parse/format yardımcıları (DD.MM.YYYY HH:MM:SS, dayfirst=True)
│   └── transforms.py      # clean_name/phone/city/school, get_next_uye_no
├── etl/
│   ├── __init__.py
│   ├── etl_member.py      # Üye CRUD ETL: extract preview, load, update (SCD1/SCD2), manual insert, deactivate
│   ├── etl_snapshot.py    # Aylık snapshot: snapshot_at_reference, preview_monthly_snapshot, sp_build_monthly_snapshot
│   └── etl_procs.py       # Re-export katmanı (geriye dönük uyumluluk için toplu import)
├── tabs/
│   ├── __init__.py
│   ├── tab_etl.py         # Formdan gelen yeni kayıtları çek / önizle / düzenle / yükle
│   ├── tab_manual.py      # Manuel üye ekleme formu
│   ├── tab_edit.py        # Aktif üyeler listesi + bilgi güncelleme + pasife alma
│   ├── tab_history.py     # Bir üyenin tüm tarihçesini gösteren ekran
│   └── tab_snapshot.py    # Aylık snapshot (rapor) oluşturma ekranı
├── tests/
│   ├── test_snapshot.py   # snapshot_at_reference fonksiyonu için birim testler (pandas DataFrame ile)
│   └── preview_snapshot.py# Komut satırından dönem verip snapshot’ı CSV olarak önizleme
├── .streamlit/
│   └── secrets.toml       # admin_password ve (Cloud’da) gcp_service_account ayarları
├── requirements.txt       # Gerekli Python paketleri
└── README.md
```

> Not: `credentials.json` dosyası (lokalde Google Service Account anahtarı) `.gitignore`
> içinde tutulmalı ve repoya asla eklenmemelidir.

---

## Kurulum ve Çalıştırma

### 1. Repoyu klonla

```bash
git clone <repository-url>
cd gencmmg-hr
```

### 2. Sanal ortam oluştur ve aktif et

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Bağımlılıkları yükle

```bash
pip install -r requirements.txt
```

`requirements.txt` içeriği kısaca:

- `streamlit`
- `gspread`
- `oauth2client`
- `pandas`

### 4. Google Sheets bağlantısını ayarla

1. Google Cloud Console’dan bir **Service Account** oluştur.
2. Sheets / Drive API yetkilerini ver.
3. Service Account için JSON key oluşturup proje köküne kaydet, adını **`credentials.json`** yap.
4. Uygulamada kullanılan Google Sheets dosyasını bu service account e‑posta adresiyle
   **“Düzenleyici (Editor)”** olarak paylaş.

Lokal geliştirmede `credentials.json` kullanılır; Streamlit Cloud üzerinde ise
`st.secrets["gcp_service_account"]` ile JSON içeriği secrets üzerinden verilebilir.

### 5. Admin şifresini tanımla

`.streamlit/secrets.toml` içinde:

```toml
admin_password = "sifre-buraya"
```

Cloud ortamında bu değer Streamlit Secrets UI üzerinden de yönetilebilir.

### 6. Uygulamayı çalıştır

```bash
streamlit run app.py
```

Tarayıcıda açılan sayfada önce admin şifresi istenir, ardından sekmeli ana ekrana yönlenirsin.

---

## Google Sheets Şema Beklentisi

Uygulama, `constants.py` içindeki `SHEET_NAME` ve çalışma sayfası (worksheet) adlarını kullanır.
Varsayılan yapı:

- **Ana dosya adı**: `gencmmg_db` (veya `SHEET_NAME` ne ise)

İçindeki sekmeler:

- **`Staging_Form`**
  - Google Form yanıtlarının doğrudan düştüğü ham tablo.
  - En azından şu alanları içerir:
    - `Zaman damgası`
    - İlgili form soruları (Adınız?, Soyadınız?, Telefon Numaranız?, …)

- **`Dim_Member_History`**
  - Asıl SCD2 tarihçe tablosu.
  - Kolon listesi `constants.HISTORY_COLUMNS` üzerinden yönetilir:
    - `uye_sk`, `uye_no`, `ilk_kayit_tarihi`, `ad`, `soyad`, `email`,
      `telefon`, `dogum_tarihi`, `yasadigi_sehir`, `uyesi_oldugu_sehir`,
      `cinsiyet`, `egitim_durumu`, `universite`, `bolum`, `sinif`,
      `rol`, `notlar`, `valid_from`, `valid_to`, `is_active`, `islenme_tarihi`

- **`Fact_Monthly_Snapshot`**
  - Aylık rapor tablosu.
  - Kolon listesi `constants.SNAPSHOT_COLUMNS` üzerinden yönetilir:
    - `data_time`, `year`, `month`, `uye_no`,
      `ad`, `soyad`, `email`, `telefon`, `dogum_tarihi`,
      `yasadigi_sehir`, `uyesi_oldugu_sehir`, `cinsiyet`, `egitim_durumu`,
      `universite`, `bolum`, `sinif`, `rol`,
      `is_active`, `islenme_tarihi`, `valid_from`, `valid_to`

---

## Geliştirici Notları

- Tüm tarih string’leri:
  - **Format**: `DD.MM.YYYY HH:MM:SS`
  - Parse ederken daima `dayfirst=True` kullanılmalı.
- Snapshot mantığı:
  - `snapshot_at_reference(df_history, reference_dt)` fonksiyonuna dayanır.
  - Birim testler `tests/test_snapshot.py` altında; PyTest olmadan da
    `python tests/test_snapshot.py` ile çalıştırılabilir.
- Tablo/arayüz görünümü:
  - `theme.py` içinde koyu arka plan + açık form/tablo kutuları ve zebra satır stili tanımlıdır.

Bu README, projeye yeni katılan bir geliştiricinin yapıyı hızlıca anlaması ve
lokalde ayağa kaldırabilmesi için yeterli olacak şekilde sade tutulmuştur.
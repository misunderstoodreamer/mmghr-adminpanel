# GencMMG IK Veri Yonetimi ve Admin Paneli

Bu proje, kurum ici insan kaynaklari ve uye verilerini yonetmek amaciyla gelistirilmis, Google Sheets'i bir veritabani (Data Warehouse) olarak kullanan sunucusuz (serverless) bir web uygulamasidir. 

Uygulama, veri muhendisligi prensiplerine uygun olarak Slowly Changing Dimensions (SCD Type 1 ve Type 2) mimarisi ile kurgulanmistir. Bu sayede uyelerin gecirdigi tum gorev, sehir ve statu degisiklikleri tarihsel olarak loglanir ve veri ambari raporlamalarina (Looker Studio vb.) hazir hale getirilir.



## Temel Ozellikler

* Otomatik ETL Sureci: Google Forms uzerinden gelen ham verilerin temizlenerek, coklama (deduplication) kontrollerinden gecirilerek ana veritabanina aktarilmasi.
* SCD Type 1 & Type 2 Guncelleme: Sehven yapilan hatalarin gecmisi bozmadan duzeltilmesi (SCD1) veya unvan/sehir degisikliklerinin eski kaydi kapatip yeni kayit acarak (SCD2) islenmesi.
* Manuel Kayit Ekleme: Form doldurmayan uyelerin sisteme manuel olarak, veri standartlarina uygun sekilde eklenmesi.
* Soft Delete (Deaktivasyon): Uyelerin sistemden fiziksel olarak silinmeden pasife alinmasi, boylece gecmis donem raporlarinin tutarliliginin korunmasi.
* Tarihce Izleme: Kurum icinde birden fazla degisiklik yasamis uyelerin kariyer ve statu cizgisinin kronolojik olarak listelenmesi.
* Guvenlik Katmani: Icerideki kisisel verileri korumak amaciyla session bazli sifreli giris ekrani.

## Teknoloji Yigini

* Uygulama Arayuzu ve Mantigi: Streamlit (Python)
* Veritabani: Google Sheets
* API Iletisimi: gspread, oauth2client
* Veri Transformasyonu: Pandas

## Proje Klasor Yapisi

├── .gitignore           # Hassas verilerin git'e basilmasini engelleyen kurallar
├── app.py               # Streamlit arayuz kodlari ve yonlendirmeler
├── credentials.json     # Google API Service Account anahtari (Git'e eklenmez)
├── db_utils.py          # Google Sheets API baglanti ve okuma/yazma fonksiyonlari
├── etl_procs.py         # ETL, veri temizleme ve SCD is mantigi fonksiyonlari
├── README.md            # Proje dokumantasyonu
└── requirements.txt     # Gerekli Python kutuphaneleri

## Kurulum ve Calistirma

### 1. Repoyu Klonlayin
```bash
git clone <repository-url>
cd <repository-folder>
2. Sanal Ortam (Virtual Environment) Olusturun ve Aktiflestirin
Bash
python -m venv venv

# Windows icin:
venv\Scripts\activate

# Mac/Linux icin:
source venv/bin/activate
3. Gerekli Kutuphaneleri Yukleyin
Bash
pip install -r requirements.txt
4. Veritabani Baglantisini Ayarlayin
Google Cloud uzerinden olusturdugunuz Service Account anahtarini (.json formati) proje ana dizinine ekleyin ve adini credentials.json olarak degistirin. Bu dosya .gitignore icinde belirtildigi icin GitHub'a gonderilmeyecektir.

5. Uygulamayi Baslatin
Bash
streamlit run app.py
Veritabani Semasi (Google Sheets)
Sistemin calismasi icin bagli olunan Google Sheets dosyasinda asagidaki sayfalarin (sekmelerin) bulunmasi gerekmektedir:

Staging_Form: Google Form yanitlarinin dogrudan dustugu ham tablo.

Dim_Member_History: Sistemin ana veri ambari tablosu. Tum aktif ve pasif kayitlar SCD2 mantigi ile (gecerlilik tarihleri ve aktiflik durumlariyla) burada tutulur.
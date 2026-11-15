# EWS Ketahanan Pangan Jawa Timur

Dashboard Early Warning System (EWS) ketahanan pangan Jawa Timur berbasis produksi padi, dibuat menggunakan Streamlit.

## Struktur project

```text
EWS_Streamlit_Jawa_Timur/
├── app.py
├── requirements.txt
├── .gitignore
├── .streamlit/
│   └── config.toml
├── assets/
│   ├── background_sawah.jpg.jfif
│   ├── logo_jatim.jfif
│   ├── logo_bps_jatim.jfif
│   └── logo_telkom.jfif
└── data/
    ├── EWS_Dashboard_Gabungan_2018_2025Q1.csv
    └── Batas_Kabupaten_Kota_Jawa_Timur.geojson
```

## Menjalankan secara lokal

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy ke Streamlit Community Cloud

1. Unggah seluruh isi folder project ini ke sebuah repository GitHub.
2. Pastikan `app.py`, `requirements.txt`, folder `data`, folder `assets`, dan `.streamlit/config.toml` ikut terunggah.
3. Buka https://share.streamlit.io/ dan masuk menggunakan GitHub.
4. Pilih **Create app**, lalu pilih repository dan branch yang benar.
5. Isi **Main file path** dengan `app.py` jika file berada di root repository.
6. Klik **Deploy** dan tunggu proses instalasi dependensi selesai.

Catatan: dashboard membaca CSV, GeoJSON, dan gambar dari folder project. Jangan mengunggah `app.py` saja tanpa folder `data` dan `assets`.

# MBG 2026 Business Intelligence Dashboard

Proyek ini adalah aplikasi dasbor interaktif berbasis Streamlit yang dikembangkan untuk memvisualisasikan data Business Intelligence (BI) secara komprehensif pada program MBG tahun 2026. Aplikasi ini memfasilitasi pemantauan metrik utama melalui antarmuka yang bersih dan responsif.

## Arsitektur & Sumber Data

Dataset utama yang menggerakkan dasbor ini (`mbg_dataset_2026.csv`) diekstrak melalui arsitektur data pipeline tingkat enterprise. Berikut adalah rincian alur teknologi yang digunakan dalam proses pengumpulan dan pengolahan data hingga siap digunakan

1. Apache NiFi (Data Ingestion) 
   Berperan sebagai jembatan penarik data dari berbagai sumber operasional. NiFi mengotomatisasi aliran data secara real-time, memastikan data mentah terdistribusi secara aman dan konsisten ke dalam pusat penyimpanan.
2. Apache Hadoop (Data Lake Storage) 
   Berfungsi sebagai infrastruktur penyimpanan terdistribusi. Data mentah yang dibawa oleh NiFi diakumulasikan di dalam Hadoop Distributed File System (HDFS), yang dirancang khusus untuk menangani skalabilitas dan redundansi data bervolume besar.
3. Dremio (Data Lakehouse Engine) 
   Bertindak sebagai mesin analitik dan kurasi data. Dremio terhubung langsung ke dalam ekosistem Hadoop untuk melakukan transformasi, agregasi, dan query data berkinerja tinggi tanpa perlu memindahkan data mentah secara fisik. Hasil query akhir dari Dremio inilah yang diekspor menjadi format `mbg_dataset_2026.csv` untuk divisualisasikan.

## Panduan Persiapan dan Instalasi

Untuk menjalankan aplikasi ini dengan optimal dan mencegah terjadinya konflik antar-library di dalam sistem komputer, sangat direkomendasikan untuk menggunakan lingkungan virtual (virtual environment). Pendekatan ini akan mengisolasi semua dependensi proyek secara mandiri.

### Prasyarat
Pastikan Python (versi 3.8 atau lebih baru) telah terinstal di komputer.

### Langkah-langkah Instalasi

1. Unduh atau lakukan clone repository ini ke komputer lokal.
2. Buka terminal atau Command Prompt, lalu arahkan direktori ke dalam folder proyek ini.
3. Buat virtual environment baru dengan menjalankan perintah berikut
   ```bash
   python -m venv .venv
5. Instal seluruh dependensi dan library pendukung melalui file requirements.txt:
   ```bash
   pip install -r requirements.txt

### Aktivasi Venv
1. Untuk sistem operasi Windows:
   ```bash
   .\.venv\Scripts\activate
2. Untuk sistem operasi macOS/Linux:
   ```bash
   source .venv/bin/activate

### Jalankan Dasbor
```bash
streamlit run app.py

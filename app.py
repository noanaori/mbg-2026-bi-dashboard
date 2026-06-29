import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import numpy as np

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="Dasbor MBG 2026 — Program Makan Bergizi Gratis",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    h1 {color: #1e3d59;}
    .stMetric {background-color: white; padding: 15px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
    .stTabs [data-baseweb="tab-list"] {gap: 8px;}
    .stTabs [data-baseweb="tab"] {
        background-color: #e9ecef;
        border-radius: 8px 8px 0 0;
        padding: 8px 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {background-color: #1e3d59; color: white;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. MEMUAT DATA
# ==========================================
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("mbg_dataset_2026.csv")
        df = df.drop_duplicates()
        return df
    except FileNotFoundError:
        st.error("File 'mbg_dataset_2026.csv' tidak ditemukan. Pastikan file berada di folder yang sama dengan aplikasi ini.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Terjadi kesalahan saat membaca data: {e}")
        return pd.DataFrame()

@st.cache_data
def load_geojson():
    try:
        with open("indonesia_provinces.json", "r") as f:
            return json.load(f)
    except Exception:
        return None

df_raw = load_data()
geojson = load_geojson()

# Pemetaan nama provinsi di dataset ke ID GeoJSON
PROV_TO_GEOID = {
    'Prov. Aceh': 1, 'Prov. Sumatera Utara': 33, 'Prov. Sumatera Barat': 31,
    'Prov. Riau': 25, 'Prov. Jambi': 9, 'Prov. Sumatera Selatan': 32,
    'Prov. Bengkulu': 5, 'Prov. Lampung': 19, 'Prov. Kepulauan Bangka Belitung': 3,
    'Prov. Kepulauan Riau': 18, 'Prov. D.K.I. Jakarta': 8, 'Prov. Jawa Barat': 10,
    'Prov. Jawa Tengah': 11, 'Prov. D.I. Yogyakarta': 34, 'Prov. Jawa Timur': 12,
    'Prov. Banten': 4, 'Prov. Bali': 2, 'Prov. Nusa Tenggara Barat': 22,
    'Prov. Nusa Tenggara Timur': 23, 'Prov. Kalimantan Barat': 13,
    'Prov. Kalimantan Tengah': 15, 'Prov. Kalimantan Selatan': 14,
    'Prov. Kalimantan Timur': 16, 'Prov. Kalimantan Utara': 35,
    'Prov. Sulawesi Utara': 30, 'Prov. Sulawesi Tengah': 28,
    'Prov. Sulawesi Selatan': 27, 'Prov. Sulawesi Tenggara': 29,
    'Prov. Sulawesi Barat': 26, 'Prov. Maluku': 21, 'Prov. Maluku Utara': 20,
    'Prov. Papua': 24,
}

JAWA_PROVINCES = [
    'Prov. Jawa Tengah', 'Prov. Jawa Timur', 'Prov. Jawa Barat',
    'Prov. D.I. Yogyakarta', 'Prov. Banten', 'Prov. D.K.I. Jakarta'
]

# ==========================================
# 3. PANEL FILTER (SIDEBAR)
# ==========================================
if not df_raw.empty:
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3081/3081330.png", width=100)
    st.sidebar.title("Panel Filter MBG")
    st.sidebar.markdown("Sesuaikan tampilan data sesuai kebutuhan Anda.")

    prov_list = sorted(df_raw['provinsi'].unique().tolist())
    selected_prov = st.sidebar.multiselect(
        "Pilih Provinsi:",
        prov_list,
        default=prov_list[:5],
        help="Pilih satu atau lebih provinsi yang ingin ditampilkan."
    )

    # Filter Kabupaten — mengikuti provinsi yang dipilih
    df_filtered_prov = df_raw[df_raw['provinsi'].isin(selected_prov)] if selected_prov else df_raw
    kab_list = sorted(df_filtered_prov['kabupaten_kota'].unique().tolist())
    selected_kab = st.sidebar.multiselect(
        "Pilih Kabupaten/Kota:",
        kab_list,
        default=[],
        help="Kosongkan untuk menampilkan semua kabupaten/kota di provinsi terpilih."
    )

    # Filter Kecamatan — mengikuti kabupaten yang dipilih
    if selected_kab:
        df_filtered_kab = df_filtered_prov[df_filtered_prov['kabupaten_kota'].isin(selected_kab)]
    else:
        df_filtered_kab = df_filtered_prov
    kec_list = sorted(df_filtered_kab['kecamatan'].unique().tolist())
    selected_kec = st.sidebar.multiselect(
        "Pilih Kecamatan:",
        kec_list,
        default=[],
        help="Kosongkan untuk menampilkan semua kecamatan di kabupaten terpilih."
    )

    jenjang_list = sorted(df_raw['jenjang'].unique().tolist())
    selected_jenjang = st.sidebar.multiselect(
        "Pilih Jenjang Pendidikan:",
        jenjang_list,
        default=jenjang_list,
        help="Filter berdasarkan tingkat pendidikan (SD, SMP, SMA, dll.)."
    )

    # Filter status sekolah (Negeri / Swasta / Semua)
    status_sekolah = st.sidebar.radio(
        "Status Sekolah:",
        options=["Semua", "Negeri Lebih Dominan", "Swasta Lebih Dominan"],
        index=0,
        help="Filter wilayah berdasarkan jenis sekolah yang mendominasi."
    )

    # Terapkan semua filter secara berantai
    mask = df_raw['provinsi'].isin(selected_prov) & df_raw['jenjang'].isin(selected_jenjang)
    if selected_kab:
        mask &= df_raw['kabupaten_kota'].isin(selected_kab)
    if selected_kec:
        mask &= df_raw['kecamatan'].isin(selected_kec)
    df = df_raw[mask].copy()

    # Terapkan filter status sekolah berdasarkan dominasi per kabupaten
    if status_sekolah != "Semua":
        df_dom = df.groupby('kabupaten_kota').agg(
            neg=('jumlah_satpen_negeri','sum'), sw=('jumlah_satpen_swasta','sum')
        ).reset_index()
        if status_sekolah == "Negeri Lebih Dominan":
            kab_filter = df_dom[df_dom['neg'] >= df_dom['sw']]['kabupaten_kota']
        else:
            kab_filter = df_dom[df_dom['sw'] > df_dom['neg']]['kabupaten_kota']
        df = df[df['kabupaten_kota'].isin(kab_filter)].copy()
    df['wilayah_grup'] = df['provinsi'].apply(
        lambda x: 'Pulau Jawa' if x in JAWA_PROVINCES else 'Luar Jawa'
    )

    # ==========================================
    # 4. JUDUL & RINGKASAN ANGKA KUNCI
    # ==========================================
    st.title("Program Makan Bergizi Gratis (MBG) 2026")
    st.markdown(
        "Dasbor ini menyajikan gambaran menyeluruh tentang **sebaran penerima manfaat**, "
        "**kesiapan sekolah**, serta **kebutuhan menu khusus** program MBG di seluruh Indonesia."
    )

    # ── Hitung semua metrik utama ──────────────────────────────────────────────
    total_penerima       = df['jumlah_penerima_manfaat'].sum()
    total_satpen         = df['jumlah_satuan_pendidikan'].sum()
    total_kondisi_khusus = df['jumlah_kondisi_khusus'].sum()
    total_laki           = df['jumlah_laki'].sum()
    total_perempuan      = df['jumlah_perempuan'].sum()
    total_negeri         = df['jumlah_satpen_negeri'].sum()
    total_swasta         = df['jumlah_satpen_swasta'].sum()
    rasio_khusus         = (total_kondisi_khusus / total_penerima * 100) if total_penerima > 0 else 0
    # Rasio kondisi khusus per 1.000 siswa
    rasio_per_seribu     = (total_kondisi_khusus / total_penerima * 1000) if total_penerima > 0 else 0
    # Gender Parity Index: perempuan / laki-laki (ideal = 1,0)
    gpi                  = (total_perempuan / total_laki) if total_laki > 0 else 0

    # ── Baris KPI 1: 4 metrik volume utama ────────────────────────────────────
    st.subheader("Ringkasan Angka Utama Program MBG")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Jumlah Penerima Manfaat", f"{total_penerima:,.0f}",
              help="Total siswa yang menerima program MBG sesuai filter aktif.")
    k2.metric("Jumlah Satuan Pendidikan", f"{total_satpen:,.0f}",
              help="Total sekolah yang terdaftar dalam program MBG.")
    k3.metric("Siswa Laki-laki", f"{total_laki:,.0f}",
              help="Jumlah siswa laki-laki penerima MBG.")
    k4.metric("Siswa Perempuan", f"{total_perempuan:,.0f}",
              help="Jumlah siswa perempuan penerima MBG.")

    # ── Baris KPI 2: metrik kondisi & sekolah ─────────────────────────────────
    k5, k6, k7, k8 = st.columns(4)
    k5.metric("Peserta Berkebutuhan Gizi Khusus", f"{total_kondisi_khusus:,.0f}",
              help="Peserta dengan alergi, fobia makanan, atau intoleransi.")
    k6.metric("Sekolah Negeri", f"{total_negeri:,.0f}",
              help="Jumlah sekolah negeri yang ikut program MBG.")
    k7.metric("Sekolah Swasta", f"{total_swasta:,.0f}",
              help="Jumlah sekolah swasta yang ikut program MBG.")
    k8.metric("Proporsi Menu Khusus", f"{rasio_khusus:.2f}%",
              help="Persen peserta yang butuh menu berbeda dari standar.")

    # ── Baris KPI 3: indikator turunan ────────────────────────────────────────
    st.caption("Indikator Tambahan (Dihitung Otomatis dari Data)")
    d1, d2, d3, d4 = st.columns(4)
    d1.metric(
        "Kebutuhan Menu Khusus per 1.000 Siswa",
        f"{rasio_per_seribu:.1f}",
        help="Dari setiap 1.000 siswa, berapa yang membutuhkan menu gizi khusus."
    )
    d2.metric(
        "Indeks Kesetaraan Gender (GPI)",
        f"{gpi:.3f}",
        help="Perbandingan jumlah siswa perempuan terhadap laki-laki. Nilai 1,0 = seimbang sempurna."
    )
    d3.metric(
        "Rata-rata Siswa per Sekolah",
        f"{(total_penerima / total_satpen):.0f}" if total_satpen > 0 else "N/A",
        help="Rata-rata beban siswa per sekolah peserta MBG."
    )
    d4.metric(
        "Porsi Sekolah Swasta",
        f"{(total_swasta / (total_negeri + total_swasta) * 100):.1f}%" if (total_negeri + total_swasta) > 0 else "N/A",
        help="Persentase sekolah swasta dari seluruh sekolah peserta MBG."
    )

    st.markdown("---")

    # ==========================================
    # 5. NAVIGASI TAB PER TEMA
    # ==========================================
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "Peta Sebaran Nasional",
        "Cakupan & Jenjang Pendidikan",
        "Ketimpangan Jawa vs. Luar Jawa",
        "Sekolah & Menu Khusus",
        "Demografi & Gender",
        "Tren & Sumber Data",
        "Peringatan & Anomali",
        "Analisis Mendalam & Simulasi"
    ])

    # ==========================================================
    # TAB 1 — PETA SEBARAN NASIONAL
    # ==========================================================
    with tab1:
        st.header("Peta Sebaran Program MBG di Seluruh Indonesia")
        st.markdown(
            "Peta di bawah memperlihatkan **seberapa besar jangkauan program MBG** di tiap provinsi. "
            "Semakin gelap warna provinsi, semakin banyak siswa yang menerima manfaat di wilayah tersebut. "
            "Provinsi berwarna abu-abu (Papua Tengah, Papua Selatan, Papua Pegunungan, Papua Barat Daya) "
            "adalah pemekaran baru yang belum tersedia dalam data peta."
        )

        if geojson:
            # Siapkan data peta
            df_map_base = df_raw.groupby('provinsi').agg(
                total_penerima=('jumlah_penerima_manfaat', 'sum'),
                total_satpen=('jumlah_satuan_pendidikan', 'sum'),
                total_kondisi=('jumlah_kondisi_khusus', 'sum'),
                total_negeri=('jumlah_satpen_negeri', 'sum'),
                total_swasta=('jumlah_satpen_swasta', 'sum'),
            ).reset_index()
            df_map_base['geo_id'] = df_map_base['provinsi'].map(PROV_TO_GEOID)
            df_map_base = df_map_base.dropna(subset=['geo_id'])
            df_map_base['geo_id'] = df_map_base['geo_id'].astype(int)
            df_map_base['nama_pendek'] = df_map_base['provinsi'].str.replace('Prov. ', '', regex=False)
            df_map_base['pct_khusus'] = (df_map_base['total_kondisi'] / df_map_base['total_penerima'] * 100).round(2)

            # --- Peta 1: Total Penerima ---
            st.subheader("Peta 1 — Jumlah Penerima Manfaat per Provinsi")
            st.caption(
                "Provinsi dengan warna biru tua adalah wilayah dengan jumlah penerima terbanyak. "
                "Arahkan kursor ke provinsi untuk melihat angka detailnya."
            )
            fig_map1 = px.choropleth(
                df_map_base,
                geojson=geojson,
                locations='geo_id',
                featureidkey='properties.id_1',
                color='total_penerima',
                hover_name='nama_pendek',
                hover_data={
                    'total_penerima': ':,',
                    'total_satpen': ':,',
                    'geo_id': False
                },
                color_continuous_scale='Blues',
                labels={
                    'total_penerima': 'Jumlah Penerima',
                    'total_satpen': 'Jumlah Sekolah'
                },
                title='Sebaran Jumlah Penerima Manfaat MBG per Provinsi'
            )
            fig_map1.update_geos(
                fitbounds="locations", visible=False,
                bgcolor='#f0f4f8'
            )
            fig_map1.update_layout(
                margin=dict(l=0, r=0, t=50, b=0),
                coloraxis_colorbar=dict(title='Penerima')
            )
            st.plotly_chart(fig_map1, key="map1", width='stretch')

            st.markdown("---")

            map_col1, map_col2 = st.columns(2)

            # --- Peta 2: Total Sekolah ---
            with map_col1:
                st.subheader("Peta 2 — Jumlah Sekolah Terdaftar")
                st.caption(
                    "Memperlihatkan berapa banyak sekolah yang ikut serta dalam program MBG di setiap provinsi."
                )
                fig_map2 = px.choropleth(
                    df_map_base,
                    geojson=geojson,
                    locations='geo_id',
                    featureidkey='properties.id_1',
                    color='total_satpen',
                    hover_name='nama_pendek',
                    hover_data={'total_satpen': ':,', 'geo_id': False},
                    color_continuous_scale='Greens',
                    labels={'total_satpen': 'Jumlah Sekolah'},
                    title='Jumlah Sekolah Peserta MBG per Provinsi'
                )
                fig_map2.update_geos(fitbounds="locations", visible=False, bgcolor='#f0f4f8')
                fig_map2.update_layout(margin=dict(l=0, r=0, t=50, b=0))
                st.plotly_chart(fig_map2, key="map2", width='stretch')

            # --- Peta 3: Proporsi Peserta Menu Khusus ---
            with map_col2:
                st.subheader("Peta 3 — Proporsi Peserta Berkebutuhan Gizi Khusus (%)")
                st.caption(
                    "Menunjukkan persentase peserta di setiap provinsi yang membutuhkan menu khusus "
                    "(alergi, fobia makanan, atau intoleransi). Semakin merah, semakin tinggi tantangan logistik katering."
                )
                fig_map3 = px.choropleth(
                    df_map_base,
                    geojson=geojson,
                    locations='geo_id',
                    featureidkey='properties.id_1',
                    color='pct_khusus',
                    hover_name='nama_pendek',
                    hover_data={'pct_khusus': ':.2f', 'total_kondisi': ':,', 'geo_id': False},
                    color_continuous_scale='OrRd',
                    labels={'pct_khusus': '% Menu Khusus', 'total_kondisi': 'Jumlah Kondisi Khusus'},
                    title='% Peserta Berkebutuhan Gizi Khusus per Provinsi'
                )
                fig_map3.update_geos(fitbounds="locations", visible=False, bgcolor='#f0f4f8')
                fig_map3.update_layout(margin=dict(l=0, r=0, t=50, b=0))
                st.plotly_chart(fig_map3, key="map3", width='stretch')

            # --- Peta 4: Dominasi Swasta ---
            st.markdown("---")
            st.subheader("Peta 4 — Porsi Sekolah Swasta dalam Program MBG (%)")
            st.caption(
                "Provinsi berwarna jingga pekat mengandalkan lebih banyak sekolah swasta untuk menjalankan program MBG. "
                "Ini penting diperhatikan karena koordinasi dengan sekolah swasta umumnya lebih kompleks."
            )
            df_map_base['pct_swasta'] = (
                df_map_base['total_swasta'] /
                (df_map_base['total_negeri'] + df_map_base['total_swasta']) * 100
            ).round(2)
            fig_map4 = px.choropleth(
                df_map_base,
                geojson=geojson,
                locations='geo_id',
                featureidkey='properties.id_1',
                color='pct_swasta',
                hover_name='nama_pendek',
                hover_data={'pct_swasta': ':.1f', 'total_swasta': ':,', 'total_negeri': ':,', 'geo_id': False},
                color_continuous_scale='Oranges',
                labels={
                    'pct_swasta': '% Sekolah Swasta',
                    'total_swasta': 'Sekolah Swasta',
                    'total_negeri': 'Sekolah Negeri'
                },
                title='Persentase Sekolah Swasta dalam Program MBG per Provinsi'
            )
            fig_map4.update_geos(fitbounds="locations", visible=False, bgcolor='#f0f4f8')
            fig_map4.update_layout(margin=dict(l=0, r=0, t=50, b=0))
            st.plotly_chart(fig_map4, key="map4", width='stretch')
        else:
            st.warning("File peta (GeoJSON) tidak ditemukan. Pastikan file 'indonesia_provinces.json' berada di folder yang sama.")

    # ==========================================================
    # TAB 2 — CAKUPAN & JENJANG PENDIDIKAN
    # ==========================================================
    with tab2:
        st.header("Cakupan Program & Komposisi Jenjang Pendidikan")
        st.markdown(
            "Bagian ini menunjukkan **sekolah mana dan tingkat pendidikan apa** yang paling banyak "
            "menerima program MBG, serta **seberapa rumit kebutuhan katering** di tiap kabupaten/kota."
        )

        row1_col1, row1_col2 = st.columns(2)

        with row1_col1:
            st.subheader("Grafik 1 — 10 Provinsi dengan Penerima Terbanyak")
            st.caption("Provinsi yang berada di bagian atas grafik adalah yang paling banyak siswanya menikmati program MBG.")
            df_prov = (
                df.groupby('provinsi')['jumlah_penerima_manfaat']
                .sum().reset_index()
                .sort_values('jumlah_penerima_manfaat', ascending=False)
                .head(10)
            )
            df_prov['nama_pendek'] = df_prov['provinsi'].str.replace('Prov. ', '', regex=False)
            fig_prov = px.bar(
                df_prov, x='jumlah_penerima_manfaat', y='nama_pendek',
                orientation='h', color='jumlah_penerima_manfaat',
                color_continuous_scale='Blues',
                labels={'jumlah_penerima_manfaat': 'Jumlah Penerima', 'nama_pendek': 'Provinsi'}
            )
            fig_prov.update_layout(yaxis={'categoryorder': 'total ascending'}, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_prov, key="g1", width='stretch')

        with row1_col2:
            st.subheader("Grafik 2 — Komposisi Jenjang Pendidikan Penerima MBG")
            st.caption(
                "Grafik ini memperlihatkan tingkat pendidikan apa yang paling banyak diwakili dalam program MBG. "
                "Klik label di legenda untuk menyembunyikan/menampilkan jenjang tertentu."
            )
            df_jenjang = df.groupby('jenjang')['jumlah_penerima_manfaat'].sum().reset_index()
            fig_jenjang = px.pie(
                df_jenjang, values='jumlah_penerima_manfaat', names='jenjang', hole=0.5,
                color_discrete_sequence=px.colors.qualitative.Pastel,
                labels={'jumlah_penerima_manfaat': 'Jumlah Penerima', 'jenjang': 'Jenjang'}
            )
            fig_jenjang.update_traces(textposition='inside', textinfo='percent+label')
            fig_jenjang.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_jenjang, key="g2", width='stretch')

        row2_col1, row2_col2 = st.columns(2)

        with row2_col1:
            st.subheader("Grafik 3 — Jumlah Sekolah: Negeri vs. Swasta")
            st.caption(
                "Perbandingan jumlah sekolah negeri dan swasta yang ikut serta dalam program MBG. "
                "Angka ini mencerminkan beban koordinasi antara pemerintah dan sektor swasta."
            )
            df_inst = pd.DataFrame({
                'Jenis Sekolah': ['Negeri', 'Swasta'],
                'Jumlah Sekolah': [df['jumlah_satpen_negeri'].sum(), df['jumlah_satpen_swasta'].sum()]
            })
            fig_inst = px.bar(
                df_inst, x='Jenis Sekolah', y='Jumlah Sekolah',
                color='Jenis Sekolah', text_auto='.2s',
                color_discrete_sequence=['#4C72B0', '#DD8452'],
                labels={'Jenis Sekolah': 'Jenis Sekolah', 'Jumlah Sekolah': 'Jumlah Sekolah'}
            )
            fig_inst.update_layout(showlegend=False, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_inst, key="g3", width='stretch')

        with row2_col2:
            st.subheader("Grafik 4 — Kerumitan Logistik Katering per Kabupaten/Kota")
            st.caption(
                "Setiap titik mewakili satu kabupaten/kota. Titik yang berada di kanan atas adalah wilayah "
                "dengan jumlah penerima banyak **sekaligus** memiliki banyak peserta berkebutuhan gizi khusus — "
                "wilayah ini memerlukan persiapan katering paling kompleks."
            )
            df_scatter = df.groupby('kabupaten_kota').agg(
                jumlah_penerima_manfaat=('jumlah_penerima_manfaat', 'sum'),
                jumlah_kondisi_khusus=('jumlah_kondisi_khusus', 'sum')
            ).reset_index()
            fig_scatter = px.scatter(
                df_scatter, x='jumlah_penerima_manfaat', y='jumlah_kondisi_khusus',
                hover_name='kabupaten_kota',
                color='jumlah_kondisi_khusus', color_continuous_scale='Reds',
                size='jumlah_penerima_manfaat',
                labels={
                    'jumlah_penerima_manfaat': 'Jumlah Penerima',
                    'jumlah_kondisi_khusus': 'Peserta Menu Khusus'
                }
            )
            fig_scatter.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_scatter, key="g4", width='stretch')

    # ==========================================================
    # TAB 3 — KETIMPANGAN JAWA VS. LUAR JAWA
    # ==========================================================
    with tab3:
        st.header("Apakah Program MBG Sudah Merata? Membandingkan Jawa dan Luar Jawa")
        st.markdown(
            "Salah satu tantangan terbesar program nasional seperti MBG adalah **ketimpangan sebaran**. "
            "Bagian ini mengulas apakah program sudah menjangkau wilayah di luar Pulau Jawa dengan proporsional."
        )

        # Grafik 5 — Treemap
        st.subheader("Grafik 5 — Peta Proporsi Penerima: Jawa vs. Luar Jawa")
        st.caption(
            "Setiap kotak mewakili satu provinsi. Semakin besar kotaknya, semakin banyak penerima manfaatnya. "
            "Kelompok biru adalah Pulau Jawa, kelompok hijau adalah Luar Jawa."
        )
        df_tree = df.groupby(['wilayah_grup', 'provinsi'])['jumlah_penerima_manfaat'].sum().reset_index()
        df_tree['nama_pendek'] = df_tree['provinsi'].str.replace('Prov. ', '', regex=False)
        fig_tree = px.treemap(
            df_tree, path=['wilayah_grup', 'nama_pendek'],
            values='jumlah_penerima_manfaat',
            color='jumlah_penerima_manfaat',
            color_continuous_scale='Blues',
            labels={'jumlah_penerima_manfaat': 'Jumlah Penerima'}
        )
        fig_tree.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_tree, key="g5", width='stretch')

        row3_col1, row3_col2 = st.columns(2)

        with row3_col1:
            st.subheader("Grafik 6 — Perbandingan Total Penerima & Sekolah: Jawa vs. Luar Jawa")
            st.caption("Grafik ini secara langsung membandingkan volume program antara Pulau Jawa dan wilayah lainnya.")
            df_gap = df.groupby('wilayah_grup').agg(
                total_penerima=('jumlah_penerima_manfaat', 'sum'),
                total_satpen=('jumlah_satuan_pendidikan', 'sum')
            ).reset_index()
            df_gap_melt = df_gap.melt(id_vars='wilayah_grup', var_name='Metrik', value_name='Jumlah')
            df_gap_melt['Metrik'] = df_gap_melt['Metrik'].map({
                'total_penerima': 'Jumlah Penerima',
                'total_satpen': 'Jumlah Sekolah'
            })
            fig_gap = px.bar(
                df_gap_melt, x='wilayah_grup', y='Jumlah', color='Metrik',
                barmode='group', text_auto='.3s',
                color_discrete_sequence=['#1f77b4', '#ff7f0e'],
                labels={'wilayah_grup': 'Wilayah', 'Jumlah': 'Total'}
            )
            fig_gap.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_gap, key="g6", width='stretch')

        with row3_col2:
            st.subheader("Grafik 7 — 10 Provinsi Luar Jawa dengan Penerima Terbanyak")
            st.caption(
                "Provinsi-provinsi ini adalah yang paling siap atau paling berpotensi untuk memperluas program MBG "
                "di luar Pulau Jawa."
            )
            df_luar_jawa = df[df['wilayah_grup'] == 'Luar Jawa']
            df_lj_prov = (
                df_luar_jawa.groupby('provinsi')['jumlah_penerima_manfaat']
                .sum().reset_index()
                .sort_values('jumlah_penerima_manfaat', ascending=False)
                .head(10)
            )
            df_lj_prov['nama_pendek'] = df_lj_prov['provinsi'].str.replace('Prov. ', '', regex=False)
            fig_lj = px.bar(
                df_lj_prov, x='jumlah_penerima_manfaat', y='nama_pendek',
                orientation='h', color='jumlah_penerima_manfaat',
                color_continuous_scale='Teal',
                labels={'jumlah_penerima_manfaat': 'Jumlah Penerima', 'nama_pendek': 'Provinsi'}
            )
            fig_lj.update_layout(yaxis={'categoryorder': 'total ascending'}, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_lj, key="g7", width='stretch')

        # Grafik 8 — Box Plot
        st.subheader("Grafik 8 — Sebaran Jumlah Penerima per Kecamatan: Jawa vs. Luar Jawa")
        st.caption(
            "Grafik kotak ini memperlihatkan seberapa merata program MBG di tingkat kecamatan. "
            "Kotak yang lebih panjang berarti lebih banyak ketimpangan antarkecamatan di wilayah tersebut. "
            "Titik-titik di luar kotak adalah kecamatan dengan angka yang jauh di atas atau di bawah rata-rata."
        )
        df_box = df.groupby(['wilayah_grup', 'kecamatan'])['jumlah_penerima_manfaat'].sum().reset_index()
        fig_box = px.box(
            df_box, x='wilayah_grup', y='jumlah_penerima_manfaat',
            color='wilayah_grup',
            color_discrete_map={'Pulau Jawa': '#1f77b4', 'Luar Jawa': '#2ca02c'},
            points='outliers',
            labels={'wilayah_grup': 'Wilayah', 'jumlah_penerima_manfaat': 'Penerima per Kecamatan'}
        )
        fig_box.update_layout(showlegend=False, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_box, key="g8", width='stretch')

    # ==========================================================
    # TAB 4 — NEGERI VS. SWASTA & KEBUTUHAN MENU KHUSUS
    # ==========================================================
    with tab4:
        # ---------- Sub-tema A: Negeri vs Swasta ----------
        st.header("Peran Sekolah Negeri dan Swasta dalam Program MBG")
        st.markdown(
            "Sekolah swasta memainkan peran penting dalam menyukseskan program MBG, terutama di daerah perkotaan. "
            "Bagian ini menganalisis seberapa besar keterlibatan mereka dan di mana dominasinya terjadi."
        )

        row4_col1, row4_col2 = st.columns(2)

        with row4_col1:
            st.subheader("Grafik 9 — Peta Dominasi Sekolah Negeri vs. Swasta per Kab/Kota")
            st.caption(
                "Setiap titik adalah satu kabupaten/kota. Warna jingga berarti sekolah swasta lebih banyak, "
                "biru berarti sekolah negeri lebih banyak. Ukuran titik menunjukkan jumlah penerima manfaat."
            )
            df_pvt = df.groupby('kabupaten_kota').agg(
                negeri=('jumlah_satpen_negeri', 'sum'),
                swasta=('jumlah_satpen_swasta', 'sum'),
                total_penerima=('jumlah_penerima_manfaat', 'sum')
            ).reset_index()
            df_pvt['Dominasi'] = df_pvt.apply(
                lambda r: 'Swasta Lebih Banyak' if r['swasta'] > r['negeri']
                else ('Seimbang' if r['swasta'] == r['negeri'] else 'Negeri Lebih Banyak'), axis=1
            )
            fig_pvt_scatter = px.scatter(
                df_pvt, x='negeri', y='swasta',
                size='total_penerima', color='Dominasi',
                hover_name='kabupaten_kota',
                color_discrete_map={
                    'Swasta Lebih Banyak': '#DD8452',
                    'Negeri Lebih Banyak': '#4C72B0',
                    'Seimbang': '#55A868'
                },
                labels={
                    'negeri': 'Jumlah Sekolah Negeri',
                    'swasta': 'Jumlah Sekolah Swasta',
                    'total_penerima': 'Jumlah Penerima'
                }
            )
            fig_pvt_scatter.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_pvt_scatter, key="g9", width='stretch')

        with row4_col2:
            st.subheader("Grafik 10 — Komposisi Sekolah Negeri vs. Swasta per Provinsi (%)")
            st.caption(
                "Grafik ini mengurutkan provinsi berdasarkan proporsi sekolah swastanya — "
                "dari yang paling banyak swasta (kiri) hingga yang paling banyak negeri (kanan)."
            )
            df_prov_inst = df.groupby('provinsi').agg(
                negeri=('jumlah_satpen_negeri', 'sum'),
                swasta=('jumlah_satpen_swasta', 'sum')
            ).reset_index()
            df_prov_inst['total'] = df_prov_inst['negeri'] + df_prov_inst['swasta']
            df_prov_inst = df_prov_inst[df_prov_inst['total'] > 0]
            df_prov_inst['pct_negeri'] = df_prov_inst['negeri'] / df_prov_inst['total'] * 100
            df_prov_inst['pct_swasta'] = df_prov_inst['swasta'] / df_prov_inst['total'] * 100
            df_prov_inst = df_prov_inst.sort_values('pct_swasta', ascending=False)
            df_prov_inst['nama_pendek'] = df_prov_inst['provinsi'].str.replace('Prov. ', '', regex=False)
            df_pct_melt = df_prov_inst.melt(
                id_vars='nama_pendek',
                value_vars=['pct_negeri', 'pct_swasta'],
                var_name='Jenis', value_name='Persentase'
            )
            df_pct_melt['Jenis'] = df_pct_melt['Jenis'].map({'pct_negeri': 'Negeri', 'pct_swasta': 'Swasta'})
            fig_pct_stack = px.bar(
                df_pct_melt, x='nama_pendek', y='Persentase', color='Jenis',
                barmode='stack',
                color_discrete_map={'Negeri': '#4C72B0', 'Swasta': '#DD8452'},
                labels={'nama_pendek': 'Provinsi', 'Persentase': 'Komposisi (%)'}
            )
            fig_pct_stack.update_layout(xaxis_tickangle=-45, margin=dict(l=0, r=0, t=10, b=100))
            st.plotly_chart(fig_pct_stack, key="g10", width='stretch')

        st.markdown("---")

        # ---------- Sub-tema B: Kebutuhan Menu Khusus ----------
        st.header("Siapa Saja yang Membutuhkan Menu Gizi Khusus?")
        st.markdown(
            "Sebagian peserta program MBG memiliki kondisi kesehatan yang membuat mereka tidak bisa mengonsumsi "
            "menu standar. Ada tiga kondisi utama yang perlu diperhatikan oleh penyelenggara katering: "
            "**alergi makanan**, **fobia makanan**, dan **intoleransi makanan**."
        )

        row5_col1, row5_col2 = st.columns(2)

        with row5_col1:
            st.subheader("Grafik 11 — Proporsi Jenis Kondisi Khusus secara Nasional")
            st.caption(
                "Dari seluruh peserta yang butuh menu khusus, grafik ini menunjukkan kondisi mana yang paling umum. "
                "Alergi makanan umumnya paling banyak dijumpai."
            )
            total_alergi = df['jumlah_alergi'].sum()
            total_fobia  = df['jumlah_fobia'].sum()
            total_intol  = df['jumlah_intoleransi'].sum()
            df_health_pie = pd.DataFrame({
                'Kondisi': ['Alergi Makanan', 'Fobia Makanan', 'Intoleransi Makanan'],
                'Jumlah':  [total_alergi, total_fobia, total_intol]
            })
            fig_health_pie = px.pie(
                df_health_pie, values='Jumlah', names='Kondisi', hole=0.45,
                color_discrete_sequence=['#e74c3c', '#e67e22', '#9b59b6'],
                labels={'Jumlah': 'Jumlah Peserta'}
            )
            fig_health_pie.update_traces(textposition='inside', textinfo='percent+label+value')
            fig_health_pie.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_health_pie, key="g11", width='stretch')

        with row5_col2:
            st.subheader("Grafik 12 — Jenis Kondisi Khusus di 10 Provinsi Teratas")
            st.caption(
                "Sepuluh provinsi dengan peserta berkebutuhan gizi khusus terbanyak, "
                "dipecah berdasarkan jenis kondisinya."
            )
            df_health_prov = df.groupby('provinsi').agg(
                alergi=('jumlah_alergi', 'sum'),
                fobia=('jumlah_fobia', 'sum'),
                intoleransi=('jumlah_intoleransi', 'sum'),
                total_kondisi=('jumlah_kondisi_khusus', 'sum')
            ).reset_index().sort_values('total_kondisi', ascending=False).head(10)
            df_health_prov['nama_pendek'] = df_health_prov['provinsi'].str.replace('Prov. ', '', regex=False)
            df_health_melt = df_health_prov.melt(
                id_vars='nama_pendek',
                value_vars=['alergi', 'fobia', 'intoleransi'],
                var_name='Jenis Kondisi', value_name='Jumlah'
            )
            df_health_melt['Jenis Kondisi'] = df_health_melt['Jenis Kondisi'].map({
                'alergi': 'Alergi', 'fobia': 'Fobia', 'intoleransi': 'Intoleransi'
            })
            fig_health_bar = px.bar(
                df_health_melt, x='nama_pendek', y='Jumlah', color='Jenis Kondisi',
                barmode='group',
                color_discrete_map={'Alergi': '#e74c3c', 'Fobia': '#e67e22', 'Intoleransi': '#9b59b6'},
                labels={'nama_pendek': 'Provinsi', 'Jumlah': 'Jumlah Peserta'}
            )
            fig_health_bar.update_layout(xaxis_tickangle=-30, margin=dict(l=0, r=0, t=10, b=80))
            st.plotly_chart(fig_health_bar, key="g12", width='stretch')

        # Grafik 13 — Bubble Scatter Korelasi
        st.subheader("Grafik 13 — Hubungan Antara Alergi, Fobia, dan Intoleransi per Kab/Kota")
        st.caption(
            "Setiap titik adalah satu kabupaten/kota. Posisi horizontal = jumlah peserta alergi, "
            "posisi vertikal = jumlah peserta fobia, dan **ukuran gelembung = jumlah peserta intoleransi**. "
            "Kabupaten/kota di sudut kanan atas memiliki tantangan gizi khusus yang paling beragam."
        )
        df_corr = df.groupby('kabupaten_kota').agg(
            alergi=('jumlah_alergi', 'sum'),
            fobia=('jumlah_fobia', 'sum'),
            intoleransi=('jumlah_intoleransi', 'sum')
        ).reset_index()
        df_corr_nonzero = df_corr[(df_corr['alergi'] > 0) | (df_corr['fobia'] > 0) | (df_corr['intoleransi'] > 0)]
        fig_corr = px.scatter(
            df_corr_nonzero, x='alergi', y='fobia',
            size='intoleransi', color='intoleransi',
            hover_name='kabupaten_kota',
            color_continuous_scale='Purples', size_max=40,
            labels={
                'alergi': 'Peserta Alergi Makanan',
                'fobia': 'Peserta Fobia Makanan',
                'intoleransi': 'Peserta Intoleransi'
            }
        )
        fig_corr.update_layout(margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig_corr, key="g13", width='stretch')

        row6_col1, row6_col2 = st.columns(2)

        with row6_col1:
            st.subheader("Grafik 14 — Rata-rata Peserta Menu Khusus per Jenjang & Wilayah")
            st.caption(
                "Grafik panas (heatmap) ini menunjukkan jenjang pendidikan mana dan di wilayah mana "
                "rata-rata peserta menu khususnya paling tinggi. Warna merah tua berarti tantangan lebih besar."
            )
            df_heat = df.groupby(['jenjang', 'wilayah_grup']).agg(
                rata_kondisi=('jumlah_kondisi_khusus', 'mean')
            ).reset_index()
            df_heat_pivot = df_heat.pivot(
                index='jenjang', columns='wilayah_grup', values='rata_kondisi'
            ).fillna(0)
            fig_heat = go.Figure(data=go.Heatmap(
                z=df_heat_pivot.values,
                x=df_heat_pivot.columns.tolist(),
                y=df_heat_pivot.index.tolist(),
                colorscale='YlOrRd',
                text=df_heat_pivot.values.round(1),
                texttemplate='%{text}',
                showscale=True,
                colorbar=dict(title='Rata-rata')
            ))
            fig_heat.update_layout(
                xaxis_title='Wilayah',
                yaxis_title='Jenjang Pendidikan',
                margin=dict(l=0, r=0, t=10, b=0)
            )
            st.plotly_chart(fig_heat, key="g14", width='stretch')

        with row6_col2:
            st.subheader("Grafik 15 — Dari Total Penerima hingga Jenis Kondisi Khusus")
            st.caption(
                "Grafik corong ini menggambarkan 'perjalanan data': dari seluruh penerima MBG, "
                "berapa yang memiliki kondisi khusus, dan kondisi apa yang paling banyak dijumpai. "
                "Semakin sempit corongnya, semakin kecil proporsinya."
            )
            total_penerima_all   = df['jumlah_penerima_manfaat'].sum()
            total_khusus_all     = df['jumlah_kondisi_khusus'].sum()
            total_alergi_all     = df['jumlah_alergi'].sum()
            total_fobia_all      = df['jumlah_fobia'].sum()
            total_intoleransi_all = df['jumlah_intoleransi'].sum()
            fig_funnel = go.Figure(go.Funnel(
                y=['Total Penerima MBG', 'Berkebutuhan Gizi Khusus',
                   'Alergi Makanan', 'Fobia Makanan', 'Intoleransi Makanan'],
                x=[total_penerima_all, total_khusus_all,
                   total_alergi_all, total_fobia_all, total_intoleransi_all],
                textinfo='value+percent initial',
                marker=dict(color=['#1f77b4', '#ff7f0e', '#e74c3c', '#e67e22', '#9b59b6'])
            ))
            fig_funnel.update_layout(margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig_funnel, key="g15", width='stretch')

    # ==========================================================
    # TAB 5 — DEMOGRAFI & GENDER
    # ==========================================================
    with tab5:
        st.header("Siapa Saja yang Menerima Program MBG?")
        st.markdown(
            "Bagian ini melihat lebih dekat **siapa penerima manfaat program MBG** dari sisi jenis kelamin "
            "dan jenjang pendidikan — untuk memastikan program ini menjangkau semua kelompok secara adil."
        )

        # ── Grafik 16: Piramida Gender per Jenjang ────────────────────────────
        st.subheader("Grafik 16 — Perbandingan Siswa Laki-laki dan Perempuan per Jenjang Pendidikan")
        st.caption(
            "Grafik ini membandingkan jumlah siswa laki-laki (kiri, biru) dan perempuan (kanan, merah muda) "
            "untuk setiap jenjang pendidikan. Batang yang seimbang menunjukkan program sudah menjangkau "
            "kedua jenis kelamin secara setara."
        )
        df_gender = df.groupby('jenjang').agg(
            laki=('jumlah_laki', 'sum'),
            perempuan=('jumlah_perempuan', 'sum')
        ).reset_index()
        # Diverging bar: laki negatif agar tampil ke kiri
        df_gender['laki_neg'] = -df_gender['laki']
        fig_pyramid = go.Figure()
        fig_pyramid.add_trace(go.Bar(
            y=df_gender['jenjang'], x=df_gender['laki_neg'],
            orientation='h', name='Laki-laki',
            marker_color='#4C72B0',
            text=df_gender['laki'].apply(lambda v: f"{v:,.0f}"),
            textposition='outside'
        ))
        fig_pyramid.add_trace(go.Bar(
            y=df_gender['jenjang'], x=df_gender['perempuan'],
            orientation='h', name='Perempuan',
            marker_color='#e74c3c',
            text=df_gender['perempuan'].apply(lambda v: f"{v:,.0f}"),
            textposition='outside'
        ))
        fig_pyramid.update_layout(
            barmode='relative',
            xaxis=dict(
                tickvals=[-df_gender['laki'].max(), -df_gender['laki'].max()//2, 0,
                           df_gender['perempuan'].max()//2, df_gender['perempuan'].max()],
                ticktext=[f"{abs(v):,.0f}" for v in
                          [-df_gender['laki'].max(), -df_gender['laki'].max()//2, 0,
                           df_gender['perempuan'].max()//2, df_gender['perempuan'].max()]],
                title="Jumlah Siswa"
            ),
            yaxis_title="Jenjang Pendidikan",
            legend=dict(orientation='h', yanchor='bottom', y=1.02),
            margin=dict(l=0, r=80, t=40, b=0)
        )
        st.plotly_chart(fig_pyramid, key="g16", use_container_width=True)

        # ── Grafik 17: GPI per Provinsi ────────────────────────────────────────
        st.subheader("Grafik 17 — Tingkat Kesetaraan Gender per Provinsi")
        st.caption(
            "Nilai di atas 1,0 berarti perempuan lebih banyak, di bawah 1,0 berarti laki-laki lebih banyak. "
            "Garis merah menandai titik keseimbangan sempurna (1,0). "
            "Semakin jauh dari garis merah, semakin besar ketimpangan gender di provinsi tersebut."
        )
        df_gpi = df.groupby('provinsi').agg(
            laki=('jumlah_laki', 'sum'),
            perempuan=('jumlah_perempuan', 'sum')
        ).reset_index()
        df_gpi['GPI'] = (df_gpi['perempuan'] / df_gpi['laki'].replace(0, np.nan)).round(3)
        df_gpi = df_gpi.dropna(subset=['GPI']).sort_values('GPI', ascending=True)
        df_gpi['nama_pendek'] = df_gpi['provinsi'].str.replace('Prov. ', '', regex=False)
        df_gpi['warna'] = df_gpi['GPI'].apply(
            lambda v: '#2ca02c' if 0.95 <= v <= 1.05 else ('#DD8452' if v > 1.05 else '#4C72B0')
        )
        fig_gpi = go.Figure()
        fig_gpi.add_trace(go.Bar(
            x=df_gpi['nama_pendek'], y=df_gpi['GPI'],
            marker_color=df_gpi['warna'],
            text=df_gpi['GPI'].apply(lambda v: f"{v:.3f}"),
            textposition='outside',
            hovertemplate="<b>%{x}</b><br>GPI: %{y:.3f}<extra></extra>"
        ))
        # Garis batas keseimbangan sempurna
        fig_gpi.add_hline(y=1.0, line_dash='dash', line_color='red',
                          annotation_text="Titik Seimbang (1,0)",
                          annotation_position="top right")
        fig_gpi.update_layout(
            xaxis_tickangle=-45,
            yaxis_title="Nilai Kesetaraan Gender (GPI)",
            xaxis_title="Provinsi",
            margin=dict(l=0, r=0, t=20, b=100)
        )
        st.plotly_chart(fig_gpi, key="g17", use_container_width=True)

        # ── Grafik 18: Stacked Bar Gender per Provinsi ────────────────────────
        r5c1, r5c2 = st.columns(2)
        with r5c1:
            st.subheader("Grafik 18 — Komposisi Gender per Provinsi (%)")
            st.caption(
                "Setiap batang mewakili satu provinsi dengan total 100%. "
                "Warna biru = laki-laki, merah = perempuan."
            )
            df_gs = df.groupby('provinsi').agg(
                laki=('jumlah_laki','sum'), perempuan=('jumlah_perempuan','sum')
            ).reset_index()
            df_gs['total'] = df_gs['laki'] + df_gs['perempuan']
            df_gs['pct_laki'] = df_gs['laki'] / df_gs['total'] * 100
            df_gs['pct_perempuan'] = df_gs['perempuan'] / df_gs['total'] * 100
            df_gs['nama_pendek'] = df_gs['provinsi'].str.replace('Prov. ','',regex=False)
            df_gs = df_gs.sort_values('pct_perempuan', ascending=False)
            fig_gs = go.Figure()
            fig_gs.add_trace(go.Bar(
                x=df_gs['nama_pendek'], y=df_gs['pct_laki'],
                name='Laki-laki', marker_color='#4C72B0'
            ))
            fig_gs.add_trace(go.Bar(
                x=df_gs['nama_pendek'], y=df_gs['pct_perempuan'],
                name='Perempuan', marker_color='#e74c3c'
            ))
            fig_gs.update_layout(
                barmode='stack', xaxis_tickangle=-45,
                yaxis_title="Komposisi (%)",
                margin=dict(l=0,r=0,t=10,b=100)
            )
            st.plotly_chart(fig_gs, key="g18", use_container_width=True)

        with r5c2:
            st.subheader("Grafik 19 — 5 Provinsi dengan Ketimpangan Gender Tertinggi")
            st.caption(
                "Tabel ini menampilkan provinsi dengan selisih terbesar antara jumlah siswa "
                "laki-laki dan perempuan — perlu perhatian khusus untuk memastikan keadilan program."
            )
            df_gpi2 = df_gpi.copy()
            df_gpi2['selisih'] = (df_gpi2['GPI'] - 1.0).abs()
            top5_gender = df_gpi2.nlargest(5, 'selisih')[
                ['nama_pendek','laki','perempuan','GPI']
            ].rename(columns={
                'nama_pendek': 'Provinsi',
                'laki': 'Siswa Laki-laki',
                'perempuan': 'Siswa Perempuan',
                'GPI': 'Nilai Kesetaraan (GPI)'
            })
            st.dataframe(top5_gender.set_index('Provinsi'), use_container_width=True)
            st.caption("GPI < 1,0 = lebih banyak laki-laki | GPI > 1,0 = lebih banyak perempuan")

    # ==========================================================
    # TAB 6 — TREN & SUMBER DATA
    # ==========================================================
    with tab6:
        st.header("Tren Pengiriman Data dan Pemantauan Sumber Laporan")
        st.markdown(
            "Tab ini memperlihatkan **kapan dan dari mana data MBG masuk** ke sistem pusat. "
            "Informasi ini berguna untuk memantau kelengkapan laporan dari setiap daerah."
        )

        # Parsing date_pull dengan format mixed
        df_tren = df.copy()
        df_tren['tanggal'] = pd.to_datetime(df_tren['date_pull'], errors='coerce')
        df_tren = df_tren.dropna(subset=['tanggal'])
        df_tren['tgl_harian'] = df_tren['tanggal'].dt.date
        df_tren['jam'] = df_tren['tanggal'].dt.hour

        # ── Grafik 20: Jumlah Data yang Masuk per Jam (Line Chart) ───────────
        st.subheader("Grafik 20 — Kecepatan Masuknya Data: Berapa Baris Data Masuk per Jam?")
        st.caption(
            "Grafik garis ini menunjukkan pada jam berapa paling banyak data dikirimkan ke sistem. "
            "Lonjakan tajam berarti banyak daerah mengirim data secara bersamaan pada jam tersebut."
        )
        df_jam = df_tren.groupby('jam').size().reset_index(name='jumlah_baris')
        fig_jam = px.line(
            df_jam, x='jam', y='jumlah_baris',
            markers=True,
            labels={'jam': 'Jam (0–23)', 'jumlah_baris': 'Jumlah Baris Data Masuk'},
            color_discrete_sequence=['#1e3d59']
        )
        fig_jam.update_layout(margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig_jam, key="g20", use_container_width=True)

        # ── Grafik 21: Kontribusi per File Sumber (Bar) ────────────────────────
        r6c1, r6c2 = st.columns(2)
        with r6c1:
            st.subheader("Grafik 21 — Berapa Banyak Data yang Dikirim Tiap Daerah?")
            st.caption(
                "Setiap batang adalah satu file kiriman dari daerah. Semakin panjang batangnya, "
                "semakin banyak data yang dilaporkan. File sangat pendek bisa berarti laporan belum lengkap."
            )
            df_src = df.groupby('__source_file').agg(
                jumlah_baris=('jumlah_penerima_manfaat','count'),
                total_penerima=('jumlah_penerima_manfaat','sum')
            ).reset_index().sort_values('jumlah_baris', ascending=True)
            # Potong nama file agar tidak terlalu panjang
            df_src['nama_file'] = df_src['__source_file'].str.replace('.csv','',regex=False).str[:40]
            fig_src = px.bar(
                df_src, x='jumlah_baris', y='nama_file',
                orientation='h', color='jumlah_baris',
                color_continuous_scale='Teal',
                labels={'jumlah_baris': 'Jumlah Baris Data', 'nama_file': 'Sumber File'}
            )
            fig_src.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig_src, key="g21", use_container_width=True)

        with r6c2:
            st.subheader("Grafik 22 — Pemeriksaan Kelengkapan Data (Nilai Kosong)")
            st.caption(
                "Grafik ini memeriksa apakah ada kolom data yang tidak terisi. "
                "Bilah merah berarti ada data yang hilang dan perlu dilengkapi."
            )
            # Hitung % missing per kolom numerik
            num_cols = ['jumlah_laki','jumlah_perempuan','jumlah_alergi','jumlah_fobia',
                        'jumlah_intoleransi','jumlah_penerima_manfaat','jumlah_kondisi_khusus',
                        'jumlah_satpen_negeri','jumlah_satpen_swasta']
            pct_missing = (df[num_cols].isnull().sum() / len(df) * 100).reset_index()
            pct_missing.columns = ['Kolom', 'Persen Kosong']
            pct_missing['Warna'] = pct_missing['Persen Kosong'].apply(
                lambda v: 'Lengkap' if v == 0 else 'Ada yang Kosong'
            )
            fig_miss = px.bar(
                pct_missing, x='Persen Kosong', y='Kolom',
                orientation='h',
                color='Warna',
                color_discrete_map={'Lengkap': '#2ca02c', 'Ada yang Kosong': '#e74c3c'},
                labels={'Persen Kosong': 'Persentase Data Kosong (%)', 'Kolom': 'Nama Kolom'}
            )
            fig_miss.update_layout(margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig_miss, key="g22", use_container_width=True)

        # ── Tabel Kondisi Analis Data Pipeline ──────────────────────────────
        st.subheader("Ringkasan Status Laporan per Sumber Data")
        st.caption("Tabel ini merangkum kondisi setiap file laporan yang masuk ke sistem.")
        df_audit = df.groupby('__source_file').agg(
            jumlah_baris=('jumlah_penerima_manfaat','count'),
            total_penerima=('jumlah_penerima_manfaat','sum'),
            total_kondisi=('jumlah_kondisi_khusus','sum'),
            missing_tanggal=('date_pull', lambda x: x.isnull().sum())
        ).reset_index()
        df_audit.columns = ['File Sumber','Jumlah Baris','Total Penerima','Total Kondisi Khusus','Data Tanggal Kosong']
        df_audit['Status'] = df_audit['Jumlah Baris'].apply(
            lambda v: 'Lengkap' if v >= 50 else ('Perlu Perhatian' if v >= 10 else 'Sangat Sedikit')
        )
        st.dataframe(df_audit.set_index('File Sumber'), use_container_width=True)

    # ==========================================================
    # TAB 7 — PERINGATAN & ANOMALI
    # ==========================================================
    with tab7:
        st.header("Pemeriksaan Data: Apakah Ada Angka yang Tidak Wajar?")
        st.markdown(
            "Tab ini secara otomatis **mencari angka yang mencurigakan** dalam data. "
            "Angka yang terlalu jauh dari rata-rata akan ditandai sebagai peringatan "
            "agar dapat diperiksa ulang oleh tim pusat."
        )

        # ── Fungsi deteksi outlier dengan batas 3 standar deviasi ─────────────
        def detect_outliers(dataframe, col, threshold=3.0):
            """Tandai baris di mana nilai kolom melebihi mean ± threshold * std."""
            mean_val = dataframe[col].mean()
            std_val  = dataframe[col].std()
            upper    = mean_val + threshold * std_val
            mask_out = dataframe[col] > upper
            return dataframe[mask_out].copy(), upper

        cols_check = {
            'jumlah_alergi':         'Alergi Makanan',
            'jumlah_fobia':          'Fobia Makanan',
            'jumlah_intoleransi':    'Intoleransi Makanan',
            'jumlah_penerima_manfaat': 'Jumlah Penerima',
            'jumlah_kondisi_khusus': 'Total Kondisi Khusus',
        }

        all_flags = []
        for col, label in cols_check.items():
            df_out, batas = detect_outliers(df, col)
            if not df_out.empty:
                df_out['Kolom Terdeteksi'] = label
                df_out['Nilai'] = df_out[col]
                df_out['Batas Wajar (Atas)'] = round(batas, 1)
                all_flags.append(df_out[['provinsi','kabupaten_kota','kecamatan','jenjang',
                                         'Kolom Terdeteksi','Nilai','Batas Wajar (Atas)']])

        if all_flags:
            df_flags = pd.concat(all_flags).sort_values('Nilai', ascending=False)
            st.error(f"Ditemukan **{len(df_flags)} baris data** dengan nilai yang jauh di atas rata-rata nasional.")
            st.caption(
                "Baris-baris ini bukan berarti salah, tetapi perlu diperiksa ulang oleh tim data. "
                "Batas wajar dihitung dari: rata-rata + 3 × simpangan baku."
            )
            st.dataframe(df_flags.reset_index(drop=True), use_container_width=True)
        else:
            st.success("Tidak ditemukan angka yang mencurigakan dalam data saat ini.")

        # ── Grafik 23: Distribusi Nilai Alergi (Histogram) ────────────────────
        st.subheader("Grafik 23 — Sebaran Jumlah Alergi per Kecamatan")
        st.caption(
            "Grafik ini memperlihatkan seberapa umum tiap angka alergi. "
            "Batang tinggi di kiri berarti kebanyakan kecamatan punya sedikit kasus alergi. "
            "Titik-titik jauh di kanan adalah kecamatan yang perlu diperiksa."
        )
        df_hist = df.groupby('kecamatan')['jumlah_alergi'].sum().reset_index()
        fig_hist = px.histogram(
            df_hist[df_hist['jumlah_alergi'] > 0],
            x='jumlah_alergi', nbins=40,
            color_discrete_sequence=['#e74c3c'],
            labels={'jumlah_alergi': 'Jumlah Peserta Alergi', 'count': 'Jumlah Kecamatan'}
        )
        # Tambah garis batas mean + 3*std
        mean_a = df_hist['jumlah_alergi'].mean()
        std_a  = df_hist['jumlah_alergi'].std()
        fig_hist.add_vline(x=mean_a + 3*std_a, line_dash='dash', line_color='red',
                           annotation_text="Batas Peringatan", annotation_position="top right")
        fig_hist.update_layout(margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig_hist, key="g23", use_container_width=True)

        # ── Grafik 24: Matriks Risiko Kontaminasi Silang ──────────────────────
        st.subheader("Grafik 24 — Peta Risiko Keamanan Dapur per Kecamatan")
        st.caption(
            "Kecamatan dengan banyak siswa alergi atau intoleransi, tetapi hanya sedikit sekolah, "
            "berarti setiap dapur menanggung beban menu khusus yang sangat besar. "
            "Kecamatan di kuadran kanan atas (risiko tinggi) perlu dapur atau area masak terpisah."
        )
        df_risk = df.groupby(['kecamatan','kabupaten_kota']).agg(
            alergi_intol=('jumlah_alergi','sum'),  # alergi + intoleransi = risiko silang
            intol=('jumlah_intoleransi','sum'),
            satpen=('jumlah_satuan_pendidikan','sum')
        ).reset_index()
        df_risk['risiko_per_sekolah'] = (
            (df_risk['alergi_intol'] + df_risk['intol']) /
            df_risk['satpen'].replace(0, np.nan)
        ).fillna(0)
        # Buat label kuadran
        med_x = df_risk['satpen'].median()
        med_y = df_risk['risiko_per_sekolah'].median()
        def label_kuadran(row):
            if row['satpen'] >= med_x and row['risiko_per_sekolah'] >= med_y:
                return 'Risiko Tinggi'
            elif row['satpen'] < med_x and row['risiko_per_sekolah'] >= med_y:
                return 'Perlu Perhatian'
            elif row['satpen'] >= med_x and row['risiko_per_sekolah'] < med_y:
                return 'Pantau'
            else:
                return 'Aman'
        df_risk['Kategori Risiko'] = df_risk.apply(label_kuadran, axis=1)
        fig_risk = px.scatter(
            df_risk, x='satpen', y='risiko_per_sekolah',
            color='Kategori Risiko',
            hover_name='kecamatan',
            hover_data={'kabupaten_kota': True, 'satpen': True, 'risiko_per_sekolah': ':.1f'},
            color_discrete_map={
                'Risiko Tinggi': '#e74c3c',
                'Perlu Perhatian': '#e67e22',
                'Pantau': '#f1c40f',
                'Aman': '#2ca02c'
            },
            labels={
                'satpen': 'Jumlah Sekolah di Kecamatan',
                'risiko_per_sekolah': 'Beban Menu Khusus per Sekolah',
                'kabupaten_kota': 'Kabupaten/Kota'
            }
        )
        # Garis batas kuadran
        fig_risk.add_vline(x=med_x, line_dash='dot', line_color='gray')
        fig_risk.add_hline(y=med_y, line_dash='dot', line_color='gray')
        fig_risk.update_layout(margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig_risk, key="g24", use_container_width=True)

    # ==========================================================
    # TAB 8 — ANALISIS MENDALAM & SIMULASI
    # ==========================================================
    with tab8:
        st.header("Analisis Mendalam & Alat Simulasi")
        st.markdown(
            "Tab ini menyajikan analisis tambahan untuk membantu pengambilan keputusan, "
            "termasuk **peringkat wilayah prioritas** dan **simulasi kebutuhan porsi makanan**."
        )

        # ── Grafik 25: Heatmap Peringkat Kondisi Khusus per Wilayah ──────────
        st.subheader("Grafik 25 — Peringkat Wilayah Berdasarkan Kondisi Khusus")
        st.caption(
            "Tabel berwarna ini membantu melihat sekaligus wilayah mana yang paling banyak "
            "memiliki peserta dengan kebutuhan gizi khusus. Semakin merah, semakin perlu perhatian."
        )
        df_rank = df.groupby(['provinsi','jenjang']).agg(
            total_kondisi=('jumlah_kondisi_khusus','sum'),
            total_penerima=('jumlah_penerima_manfaat','sum')
        ).reset_index()
        df_rank['pct_kondisi'] = (df_rank['total_kondisi'] / df_rank['total_penerima'] * 100).round(2)
        df_rank_pivot = df_rank.pivot_table(
            index='provinsi', columns='jenjang', values='pct_kondisi', aggfunc='mean'
        ).fillna(0)
        df_rank_pivot.index = df_rank_pivot.index.str.replace('Prov. ','',regex=False)
        fig_heatmap_rank = go.Figure(data=go.Heatmap(
            z=df_rank_pivot.values,
            x=df_rank_pivot.columns.tolist(),
            y=df_rank_pivot.index.tolist(),
            colorscale='YlOrRd',
            text=np.round(df_rank_pivot.values, 1),
            texttemplate='%{text}%',
            showscale=True,
            colorbar=dict(title='% Kondisi Khusus')
        ))
        fig_heatmap_rank.update_layout(
            xaxis_title='Jenjang Pendidikan',
            yaxis_title='Provinsi',
            margin=dict(l=0,r=0,t=10,b=0),
            height=600
        )
        st.plotly_chart(fig_heatmap_rank, key="g25", use_container_width=True)

        st.markdown("---")

        # ── Grafik 26: Top 5 Wilayah Prioritas Intervensi ─────────────────────
        st.subheader("Grafik 26 — 5 Wilayah yang Paling Perlu Mendapat Perhatian Segera")
        st.caption(
            "Wilayah dipilih berdasarkan gabungan tiga faktor: "
            "banyaknya peserta berkebutuhan gizi khusus, tingginya proporsi menu khusus, "
            "dan banyaknya jumlah penerima manfaat. Skor akhir dihitung otomatis dari data."
        )
        df_prio = df.groupby('kabupaten_kota').agg(
            total_penerima=('jumlah_penerima_manfaat','sum'),
            total_kondisi=('jumlah_kondisi_khusus','sum'),
            total_alergi=('jumlah_alergi','sum'),
            total_fobia=('jumlah_fobia','sum'),
            total_intol=('jumlah_intoleransi','sum'),
            total_satpen=('jumlah_satuan_pendidikan','sum')
        ).reset_index()
        # Formula skor prioritas (pembobotan): bobot kondisi lebih tinggi
        df_prio['skor'] = (
            0.40 * (df_prio['total_kondisi'] / df_prio['total_kondisi'].max()) +
            0.35 * (df_prio['total_penerima'] / df_prio['total_penerima'].max()) +
            0.25 * ((df_prio['total_kondisi'] / df_prio['total_penerima'].replace(0,1)))
        ).round(4)
        top5_prio = df_prio.nlargest(5, 'skor')[
            ['kabupaten_kota','total_penerima','total_kondisi','total_satpen','skor']
        ].rename(columns={
            'kabupaten_kota': 'Kabupaten/Kota',
            'total_penerima': 'Jumlah Penerima',
            'total_kondisi': 'Peserta Gizi Khusus',
            'total_satpen': 'Jumlah Sekolah',
            'skor': 'Skor Prioritas (0–1)'
        })
        st.dataframe(top5_prio.set_index('Kabupaten/Kota'), use_container_width=True)

        fig_prio = px.bar(
            top5_prio.sort_values('Skor Prioritas (0–1)'),
            x='Skor Prioritas (0–1)', y='Kabupaten/Kota',
            orientation='h', color='Skor Prioritas (0–1)',
            color_continuous_scale='Reds',
            text='Skor Prioritas (0–1)',
            labels={'Kabupaten/Kota': 'Wilayah', 'Skor Prioritas (0–1)': 'Skor Prioritas'}
        )
        fig_prio.update_traces(texttemplate='%{text:.4f}', textposition='outside')
        fig_prio.update_layout(margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig_prio, key="g26", use_container_width=True)

        st.markdown("---")

        # ── Grafik 27: Analisis Kesenjangan Layanan (Gap Analysis) ────────────
        st.subheader("Grafik 27 — Apakah Jumlah Penerima Seimbang dengan Jumlah Sekolah?")
        st.caption(
            "Grafik ini membandingkan jumlah penerima manfaat dan jumlah sekolah di setiap provinsi. "
            "Titik yang jauh dari garis tengah (merah putus-putus) menunjukkan ketidakseimbangan: "
            "terlalu banyak siswa untuk jumlah sekolah yang ada, atau sebaliknya."
        )
        df_gap2 = df.groupby('provinsi').agg(
            total_penerima=('jumlah_penerima_manfaat','sum'),
            total_satpen=('jumlah_satuan_pendidikan','sum')
        ).reset_index()
        df_gap2['nama_pendek'] = df_gap2['provinsi'].str.replace('Prov. ','',regex=False)
        df_gap2['siswa_per_sekolah'] = df_gap2['total_penerima'] / df_gap2['total_satpen'].replace(0,1)
        # Tambah garis regresi
        x_vals = df_gap2['total_satpen'].values
        y_vals = df_gap2['total_penerima'].values
        slope, intercept, r_val, _, _ = np.polyfit(x_vals, y_vals, 1, full=False), 0, 0, 0, 0
        slope_r, intercept_r = np.polyfit(x_vals, y_vals, 1)
        x_line = np.linspace(x_vals.min(), x_vals.max(), 100)
        y_line = slope_r * x_line + intercept_r
        fig_gap2 = px.scatter(
            df_gap2, x='total_satpen', y='total_penerima',
            text='nama_pendek', color='siswa_per_sekolah',
            color_continuous_scale='RdYlGn_r',
            labels={
                'total_satpen': 'Jumlah Sekolah',
                'total_penerima': 'Jumlah Penerima Manfaat',
                'siswa_per_sekolah': 'Siswa per Sekolah'
            },
            size='total_penerima', size_max=30
        )
        fig_gap2.add_trace(go.Scatter(
            x=x_line, y=y_line, mode='lines',
            line=dict(dash='dash', color='red', width=2),
            name='Garis Tren'
        ))
        fig_gap2.update_traces(textposition='top center', selector=dict(mode='markers+text'))
        fig_gap2.update_layout(margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig_gap2, key="g27", use_container_width=True)

        st.markdown("---")

        # ── Widget 28: Simulasi Kebutuhan Porsi Makanan ────────────────────────
        st.subheader("Simulasi: Berapa Porsi Makanan yang Dibutuhkan Jika Jumlah Penerima Bertambah?")
        st.caption(
            "Gunakan penggeser di bawah untuk mensimulasikan kebutuhan porsi makanan "
            "jika program MBG diperluas ke lebih banyak siswa."
        )

        sim_c1, sim_c2 = st.columns([1, 2])
        with sim_c1:
            pct_naik = st.slider(
                "Kenaikan Jumlah Penerima (%)",
                min_value=0, max_value=50, value=10, step=5,
                help="Geser untuk mensimulasikan kenaikan jumlah penerima manfaat."
            )
            hari_per_minggu = st.slider(
                "Hari Pembagian Makan per Minggu",
                min_value=1, max_value=7, value=5, step=1,
                help="Biasanya program MBG berjalan 5 hari kerja per minggu."
            )
            biaya_per_porsi = st.number_input(
                "Estimasi Biaya per Porsi (Rp)",
                min_value=5000, max_value=50000, value=15000, step=1000,
                help="Masukkan estimasi biaya satu porsi makan bergizi."
            )

        with sim_c2:
            penerima_saat_ini = total_penerima
            penerima_simulasi = penerima_saat_ini * (1 + pct_naik / 100)
            tambahan_penerima = penerima_simulasi - penerima_saat_ini

            porsi_harian_skrg     = penerima_saat_ini
            porsi_harian_sim      = penerima_simulasi
            porsi_mingguan_skrg   = penerima_saat_ini * hari_per_minggu
            porsi_mingguan_sim    = penerima_simulasi * hari_per_minggu
            porsi_bulanan_skrg    = porsi_mingguan_skrg * 4
            porsi_bulanan_sim     = porsi_mingguan_sim  * 4

            biaya_bulanan_skrg    = porsi_bulanan_skrg * biaya_per_porsi
            biaya_bulanan_sim     = porsi_bulanan_sim  * biaya_per_porsi
            selisih_biaya         = biaya_bulanan_sim - biaya_bulanan_skrg

            st.markdown(f"#### Hasil Simulasi: Kenaikan **{pct_naik}%** Penerima Manfaat")

            s1, s2, s3 = st.columns(3)
            s1.metric("Jumlah Penerima Saat Ini",    f"{penerima_saat_ini:,.0f}")
            s2.metric("Jumlah Penerima Setelah Naik", f"{penerima_simulasi:,.0f}",
                      delta=f"+{tambahan_penerima:,.0f} siswa baru")
            s3.metric("Tambahan Porsi per Hari",      f"{tambahan_penerima:,.0f}")

            s4, s5, s6 = st.columns(3)
            s4.metric("Porsi per Minggu (sekarang)",  f"{porsi_mingguan_skrg:,.0f}")
            s5.metric("Porsi per Minggu (simulasi)",  f"{porsi_mingguan_sim:,.0f}")
            s6.metric("Porsi per Bulan (simulasi)",   f"{porsi_bulanan_sim:,.0f}")

            s7, s8 = st.columns(2)
            s7.metric("Estimasi Biaya Bulanan (sekarang)", f"Rp {biaya_bulanan_skrg:,.0f}")
            s8.metric("Estimasi Biaya Bulanan (simulasi)",  f"Rp {biaya_bulanan_sim:,.0f}",
                      delta=f"+Rp {selisih_biaya:,.0f}")

            # Grafik perbandingan simulasi
            df_sim = pd.DataFrame({
                'Kondisi': ['Saat Ini', f'Naik {pct_naik}%'],
                'Porsi per Bulan': [porsi_bulanan_skrg, porsi_bulanan_sim],
                'Biaya per Bulan (Rp)': [biaya_bulanan_skrg, biaya_bulanan_sim]
            })
            fig_sim = px.bar(
                df_sim.melt(id_vars='Kondisi', var_name='Kategori', value_name='Nilai'),
                x='Kondisi', y='Nilai', color='Kategori',
                barmode='group',
                color_discrete_sequence=['#1e3d59','#e74c3c'],
                text_auto='.3s',
                labels={'Nilai':'Jumlah', 'Kondisi':'Skenario'}
            )
            fig_sim.update_layout(margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig_sim, key="g28", use_container_width=True)

else:
    st.warning("Data belum berhasil dimuat. Silakan periksa apakah file 'mbg_dataset_2026.csv' sudah berada di folder yang sama dengan aplikasi ini.")

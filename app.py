import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

# ==========================================
# 1. KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="Dasbor MBG 2026 — Program Makan Bergizi Gratis",
    page_icon="🍱",
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

    jenjang_list = sorted(df_raw['jenjang'].unique().tolist())
    selected_jenjang = st.sidebar.multiselect(
        "Pilih Jenjang Pendidikan:",
        jenjang_list,
        default=jenjang_list,
        help="Filter berdasarkan tingkat pendidikan (SD, SMP, SMA, dll.)."
    )

    mask = (df_raw['provinsi'].isin(selected_prov)) & (df_raw['jenjang'].isin(selected_jenjang))
    df = df_raw[mask]
    df = df.copy()
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

    total_penerima    = df['jumlah_penerima_manfaat'].sum()
    total_satpen      = df['jumlah_satuan_pendidikan'].sum()
    total_kondisi_khusus = df['jumlah_kondisi_khusus'].sum()
    rasio_khusus      = (total_kondisi_khusus / total_penerima * 100) if total_penerima > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Jumlah Penerima Manfaat",   f"{total_penerima:,.0f}",
                help="Total siswa/peserta didik yang menerima program MBG.")
    col2.metric("Jumlah Satuan Pendidikan",  f"{total_satpen:,.0f}",
                help="Total sekolah/satuan pendidikan yang terdaftar dalam program.")
    col3.metric("Peserta Berkebutuhan Gizi Khusus", f"{total_kondisi_khusus:,.0f}",
                help="Peserta yang memiliki kondisi khusus (alergi, fobia makanan, atau intoleransi).")
    col4.metric("Proporsi Menu Khusus",      f"{rasio_khusus:.2f}%",
                help="Persentase peserta yang membutuhkan penyesuaian menu dari katering.")

    st.markdown("---")

    # ==========================================
    # 5. NAVIGASI TAB PER TEMA
    # ==========================================
    tab1, tab2, tab3, tab4 = st.tabs([
        "Peta Sebaran Nasional",
        "Cakupan & Jenjang Pendidikan",
        "Ketimpangan Jawa vs. Luar Jawa",
        "Sekolah Negeri vs. Swasta & Kebutuhan Menu Khusus"
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

else:
    st.warning("Data belum berhasil dimuat. Silakan periksa apakah file 'MASTER_DATASET_MBG_BI2026.csv' sudah berada di folder yang sama dengan aplikasi ini.")

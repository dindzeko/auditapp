import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import datetime

# Fungsi untuk menambahkan CSS
def add_css(css):
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# CSS styling (opsional)
css_styles = """
<style>
/* Styling untuk judul utama */
h1 {
    font-size: 2.5rem;
    color: #333;
}

/* Styling untuk deskripsi */
p {
    font-size: 1.2rem;
    color: #555;
}

/* Styling untuk sidebar */
.sidebar .sidebar-content {
    padding: 20px;
    background-color: #f9f9f9;
}
</style>
"""
add_css(css_styles)

# Impor modul-modul halaman dari folder `page/`
try:
    from page.batchsemesteran import batchsemesteran_app
except ImportError as e:
    st.error(f"Error importing modules: {str(e)}")
    st.stop()

# Inisialisasi session state
if "subpage" not in st.session_state:
    st.session_state["subpage"] = None

# ----------- HALAMAN UTAMA -----------
def main_page():
    st.title("Selamat Datang di AuditApp!")
    st.write("""
    Aplikasi ini dirancang untuk membantu mempermudah pekerjaan Audit. 
    Di halaman utama ini, Anda akan menemukan informasi dasar dan panduan untuk memulai.
    
    Modul yang tersedia:
    - **Depresiasi**: Hitung penyusutan aset tetap.
    - **Sample**: Pengambilan sampel data audit.
    - **Fuzzy Searching**: Pencarian data dengan toleransi typo.
    - **Buku Besar**: Halaman khusus mencari rincian buku besar LKTangcit.
    - **PDF Tools**: Manipulasi dokumen PDF.
    - **FIFO**: Perhitungan persediaan metode FIFO.
    - **GPS**: Menghasilkan KML file dari foto atau gambar.
    - **RecalTab**: Pengecekan tabel di file laporan berbentuk Ms Word.
    """)

# ----------- HALAMAN DEPRESIASI -----------
def depresiasi():
    st.title("Rekalkulasi Penyusutan Aset Tetap")
    
    # Membagi layout menjadi 4 kolom
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Susut Tahunan", use_container_width=True):
            st.session_state["subpage"] = "Susut Tahunan"
    with col2:
        if st.button("Susut Semester", use_container_width=True):
            st.session_state["subpage"] = "Susut Semester"
    with col3:
        if st.button("Batch Tahunan", use_container_width=True):
            st.session_state["subpage"] = "Batch Tahunan"
    with col4:
        if st.button("Batch Semesteran", use_container_width=True):
            st.session_state["subpage"] = "Batch Semesteran"
            
    # Render subpage sesuai session state
    if st.session_state["subpage"] == "Batch Semesteran":
        try:
            batchsemesteran_app()
        except Exception as e:
            st.error(f"Error: {str(e)}")

# ----------- KONFIGURASI NAVIGASI -----------
page_config = {
    "Main Page": main_page,
    "Depresiasi": depresiasi,
}

# ----------- SIDEBAR -----------
with st.sidebar:
    selected = option_menu(
        menu_title="AuditApp",
        options=list(page_config.keys()),
        icons=[
            "house", "calculator"
        ],
        menu_icon="cast",
        default_index=0,
    )

# Reset session state jika kembali ke halaman utama
if selected == "Main Page":
    st.session_state["subpage"] = None

# ----------- RENDER HALAMAN -----------
try:
    if selected in page_config:
        page_config[selected]()
    else:
        st.error("Halaman tidak ditemukan. Silakan pilih halaman lain dari menu navigasi.")
except KeyError as e:
    st.error(f"Kesalahan: Halaman '{selected}' tidak ditemukan.")
except Exception as e:
    st.error(f"Terjadi kesalahan: {str(e)}")

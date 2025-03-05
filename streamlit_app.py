import streamlit as st
from streamlit_option_menu import option_menu

# Fungsi untuk menambahkan CSS
def add_css(css):
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# CSS styling (kosongkan dulu untuk fokus perbaikan fungsional)
css_styles = ""
add_css(css_styles)

# Impor modul dengan koreksi typo
try:
    from page.susuttahunan import app as susuttahunan_app
    from page.susutsemester import app as susutsemester_app
    from page.ahp import app as ahp_app
    from page.mus import app as mus_app
    from page.benfords import app as benfords_app
    from page.fifoindividu import app as fifoindividu_app  # Perbaiki typo 'impor t'
    from page.fifobatch import app as fifobatch_app
    from page.mergepdf import app as mergepdf_app
    from page.extractpdf import app as extractpdf_app  # Perbaiki typo 'extractpdf_ap p'
    from page.fuzzysearch import app as fuzzysearch_app
    from page.querybuilder import app as querybuilder_app
    from page.gps import app as gps_app
    from page.recaltab import app as recaltab_app  # Ganti dari 'ceklhp' ke 'recaltab'
except ImportError as e:
    st.error(f"Error importing modules: {str(e)}")
    st.stop()

# Inisialisasi session state
if "subpage" not in st.session_state:
    st.session_state["subpage"] = None

# ----------- HALAMAN UTAMA -----------
def main_page():
    st.title("Selamat Datang!")
    st.write("""
    Aplikasi ini dirancang untuk membantu mempermudah pekerjaan Audit. 
    Di halaman utama ini, Anda akan menemukan informasi dasar dan panduan untuk memulai.
    
    Modul yang tersedia:
    - **Depresiasi**: Hitung penyusutan aset
    - **Sample**: Pengambilan sampel data audit
    - **Fuzzy Searching**: Pencarian data dengan toleransi typo
    - **Query Builder**: Membuat kueri database visual
    - **PDF Tools**: Manipulasi dokumen PDF
    - **FIFO**: Perhitungan persediaan metode FIFO
    - **GPS**:menghasilkan KML File dari Foto atau Image
    - **RecalTab**: Pengecekan tabel di File atau Laporan berbentuk Ms Word
    """)

# ----------- HALAMAN DEPRESIASI -----------
def depresiasi():
    st.title("Rekalkulasi Penyusutan Aset Tetap")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Susut Tahunan", use_container_width=True):
            st.session_state["subpage"] = "Susut Tahunan"
    with col2:
        if st.button("Susut Semester", use_container_width=True):
            st.session_state["subpage"] = "Susut Semester"
    
    if st.session_state["subpage"] == "Susut Tahunan":
        try:
            susuttahunan_app()
        except Exception as e:
            st.error(f"Error: {str(e)}")
    elif st.session_state["subpage"] == "Susut Semester":
        try:
            susutsemester_app()
        except Exception as e:
            st.error(f"Error: {str(e)}")

# ----------- HALAMAN SAMPLE -----------
def sample():
    st.title("Pengambilan Sampel")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("AHP", use_container_width=True):
            st.session_state["subpage"] = "AHP"
    with col2:
        if st.button("MUS", use_container_width=True):
            st.session_state["subpage"] = "MUS"
    with col3:
        if st.button("Benford's Law", use_container_width=True):
            st.session_state["subpage"] = "Benford's Law"
    
    if st.session_state["subpage"] == "AHP":
        st.subheader("Analytic Hierarchy Process")
        ahp_app()
    elif st.session_state["subpage"] == "MUS":
        st.subheader("Monetary Unit Sampling")
        mus_app()
    elif st.session_state["subpage"] == "Benford's Law":
        st.subheader("Benford's Law Analysis")
        benfords_app()

# ----------- HALAMAN PDF TOOLS -----------
def pdf_tools():
    st.title("PDF Tools")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Gabungkan PDF", use_container_width=True):
            st.session_state["subpage"] = "Merge PDF"
    with col2:
        if st.button("Ekstrak PDF", use_container_width=True):
            st.session_state["subpage"] = "Extract PDF"
    
    if st.session_state["subpage"] == "Merge PDF":
        st.subheader("Gabung File PDF")
        mergepdf_app()
    elif st.session_state["subpage"] == "Extract PDF":
        st.subheader("Ekstrak Halaman PDF")
        extractpdf_app()

# ----------- HALAMAN FIFO -----------
def fifo():
    st.title("FIFO Inventory Calculator")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Input Manual", use_container_width=True):
            st.session_state["subpage"] = "Individu"
    with col2:
        if st.button("Upload Excel", use_container_width=True):
            st.session_state["subpage"] = "Batch"
    
    if st.session_state["subpage"] == "Individu":
        st.subheader("Metode Manual")
        fifoindividu_app()
    elif st.session_state["subpage"] == "Batch":
        st.subheader("Metode Batch")
        fifobatch_app()

# ----------- HALAMAN LAINNYA -----------
def fuzzy_searching():
    st.title("Fuzzy Searching")
    fuzzysearch_app()

def query_builder():
    st.title("Query Builder")
    querybuilder_app()

def gps():
    st.title("🌍 KML Generator")
    gps_app()

def recaltab():  # Ganti dari 'ceklhp' ke 'recaltab'
    st.title("📝 RecalTab")
    recaltab_app()  # Ganti dari 'ceklhp_app' ke 'recaltab_app'

# ----------- KONFIGURASI NAVIGASI -----------
page_config = {
    "Main Page": main_page,
    "Depresiasi": depresiasi,
    "Sample": sample,
    "Fuzzy Searching": fuzzy_searching,
    "Query Builder": query_builder,
    "PDF Tools": pdf_tools,
    "FIFO": fifo,
    "GPS": gps,
    "RecalTab": recaltab,  # Ganti dari 'ceklhp' ke 'recaltab'
}

# ----------- SIDEBAR -----------
with st.sidebar:
    selected = option_menu(
        menu_title="AuditApp",
        options=list(page_config.keys()),
        icons=[
            "house", "calculator", "clipboard-data", "search",
            "code-slash", "file-earmark-pdf", "box",
            "geo-alt", "file-earmark-check"
        ],
        menu_icon="cast",
        default_index=0,
    )

# ----------- RENDER HALAMAN -----------
if selected in page_config:
    page_config[selected]()
else:
    st.error("Halaman tidak ditemukan")

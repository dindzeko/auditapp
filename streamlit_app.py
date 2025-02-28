import streamlit as st
from streamlit_option_menu import option_menu

# Fungsi untuk menambahkan CSS
def add_css(css):
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# CSS styling
css_styles = """
<style>
.fade-in { animation: fadeIn 0.5s ease-in-out; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.sidebar .sidebar-content {
    background-color: #ffffff;
    border-right: 1px solid #eaeaea;
    padding: 20px;
    box-shadow: 2px 0 6px rgba(0,0,0,0.05);
}

.main-content {
    padding: 20px;
    background-color: #f9f9f9;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin: 20px 0;
    text-align: center;
}

button {
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    cursor: pointer;
    transition: all 0.3s;
}

button:hover {
    background-color: #0056b3;
    transform: scale(1.05);
}
</style>
"""
add_css(css_styles)

# Impor modul dengan error handling
try:
    from page.susuttahunan import app as susuttahunan_app
    from page.susutsemester import app as susutsemester_app
    from page.ahp import app as ahp_app
    from page.mus import app as mus_app
    from page.benfords import app as benfords_app
    from page.fifoindividu import app as fifoindividu_app
    from page.fifobatch import app as fifobatch_app
    from page.mergepdf import app as mergepdf_app
    from page.extractpdf import app as extractpdf_app
    from page.fuzzysearch import app as fuzzysearch_app
    from page.querybuilder import app as querybuilder_app
    from page.gps import app as gps_app
    from page.ceklhp import app as ceklhp_app
except ImportError as e:
    st.error(f"Error modul: {str(e)}")
    st.stop()

# Inisialisasi session state
if "subpage" not in st.session_state:
    st.session_state.subpage = None

# ----------- DEFINISI HALAMAN -----------
def main_page():
    with st.container():
        st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
        st.title("Selamat Datang di AuditApp!")
        st.write("Aplikasi all-in-one untuk kebutuhan audit dengan fitur:")
        st.markdown("""
        - 📉 **Depresiasi** - Hitung penyusutan aset
        - 📊 **Sample** - Pengambilan sampel data
        - 🔍 **Fuzzy Search** - Pencarian cerdas
        - 🗄️ **Query Builder** - Bangun kueri database
        - 📄 **PDF Tools** - Manipulasi dokumen
        - 📦 **FIFO** - Perhitungan persediaan
        - 🌍 **GPS** - Analisis geospasial
        - ✅ **Cek LHP** - Verifikasi laporan
        """)
        st.markdown('</div>', unsafe_allow_html=True)

def depresiasi():
    with st.container():
        st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
        st.title("Rekalkulasi Penyusutan Aset")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Hitung Tahunan", use_container_width=True):
                st.session_state.subpage = "Susut Tahunan"
        with col2:
            if st.button("Hitung Semester", use_container_width=True):
                st.session_state.subpage = "Susut Semester"
        
        if st.session_state.subpage == "Susut Tahunan":
            st.subheader("Metode Tahunan")
            susuttahunan_app()
        elif st.session_state.subpage == "Susut Semester":
            st.subheader("Metode Semester")
            susutsemester_app()
        
        st.markdown('</div>', unsafe_allow_html=True)

def sample():
    with st.container():
        st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
        st.title("Pengambilan Sampel")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("AHP", use_container_width=True):
                st.session_state.subpage = "AHP"
        with col2:
            if st.button("MUS", use_container_width=True):
                st.session_state.subpage = "MUS"
        with col3:
            if st.button("Benford's", use_container_width=True):
                st.session_state.subpage = "Benford's Law"
        
        if st.session_state.subpage == "AHP":
            st.subheader("Analytic Hierarchy Process")
            ahp_app()
        elif st.session_state.subpage == "MUS":
            st.subheader("Monetary Unit Sampling")
            mus_app()
        elif st.session_state.subpage == "Benford's Law":
            st.subheader("Benford's Law Analysis")
            benfords_app()
        
        st.markdown('</div>', unsafe_allow_html=True)

def pdf_tools():
    with st.container():
        st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
        st.title("PDF Tools")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Gabungkan PDF", use_container_width=True):
                st.session_state.subpage = "Merge PDF"
        with col2:
            if st.button("Ekstrak PDF", use_container_width=True):
                st.session_state.subpage = "Extract PDF"
        
        if st.session_state.subpage == "Merge PDF":
            st.subheader("Gabung File PDF")
            mergepdf_app()
        elif st.session_state.subpage == "Extract PDF":
            st.subheader("Ekstrak Halaman PDF")
            extractpdf_app()
        
        st.markdown('</div>', unsafe_allow_html=True)

def fifo():
    with st.container():
        st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
        st.title("Kalkulator FIFO")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Input Manual", use_container_width=True):
                st.session_state.subpage = "Individu"
        with col2:
            if st.button("Upload Excel", use_container_width=True):
                st.session_state.subpage = "Batch"
        
        if st.session_state.subpage == "Individu":
            st.subheader("Metode Manual")
            fifoindividu_app()
        elif st.session_state.subpage == "Batch":
            st.subheader("Metode Batch")
            fifobatch_app()
        
        st.markdown('</div>', unsafe_allow_html=True)

def fuzzy_searching():
    with st.container():
        st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
        st.title("Pencarian Fuzzy")
        fuzzysearch_app()
        st.markdown('</div>', unsafe_allow_html=True)

def query_builder():
    with st.container():
        st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
        st.title("Pembuat Query")
        querybuilder_app()
        st.markdown('</div>', unsafe_allow_html=True)

def gps():
    with st.container():
        st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
        st.title("Analisis GPS")
        gps_app()
        st.markdown('</div>', unsafe_allow_html=True)

def cek_lhp():
    with st.container():
        st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
        st.title("Verifikasi LHP")
        ceklhp_app()
        st.markdown('</div>', unsafe_allow_html=True)

# ----------- NAVIGASI UTAMA -----------
page_config = {
    "Main Page": main_page,
    "Depresiasi": depresiasi,
    "Sample": sample,
    "Fuzzy Searching": fuzzy_searching,
    "Query Builder": query_builder,
    "PDF Tools": pdf_tools,
    "FIFO": fifo,
    "GPS": gps,
    "Cek LHP": cek_lhp,
}

# Sidebar dengan ikon
with st.sidebar:
    selected = option_menu(
        menu_title="AuditApp",
        options=list(page_config.keys()),
        icons=[
            "house", "calculator", "clipboard-data", "search", 
            "code-slash", "file-earmark-pdf", "box", 
            "geo-alt", "clipboard-check"
        ],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important"},
            "nav": {"background-color": "#f0f2f6"},
            "icon": {"color": "#007bff"},
            "nav-item": {"margin": "5px 0"},
        }
    )

# Render halaman
if selected in page_config:
    page_config[selected]()
else:
    st.error("Halaman tidak ditemukan")

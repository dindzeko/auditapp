import streamlit as st
from streamlit_option_menu import option_menu

# Fungsi untuk menambahkan CSS ke aplikasi Streamlit
def add_css(css):
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# CSS tambahan untuk gaya animasi dan sidebar
css_styles = """
<style>
/* Animasi fade-in */
.fade-in {
    animation: fadeIn 0.5s ease-in-out;
}
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
/* Gaya Sidebar */
.sidebar .sidebar-content {
    background-color: #ffffff;
    border-right: 1px solid #eaeaea;
    padding: 20px;
    box-shadow: 2px 0 6px rgba(0, 0, 0, 0.05);
}
/* Konten utama styling */
.main-content {
    padding: 20px;
    background-color: #f9f9f9;
    border-radius: 12px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    margin: 20px 0;
    text-align: center;
}
/* Efek Hover pada Tombol */
button {
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    cursor: pointer;
    transition: all 0.3s ease-in-out;
}
button:hover {
    background-color: #0056b3;
    transform: scale(1.05);
}
/* Styling Tabs */
.tabs {
    display: flex;
    justify-content: center;
    gap: 20px;
    margin-bottom: 20px;
}
.tabs button {
    background-color: #eaeaea;
    color: #333;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    cursor: pointer;
    transition: all 0.3s ease-in-out;
}
.tabs button.active {
    background-color: #007bff;
    color: white;
}
</style>
"""

# Tambahkan CSS
add_css(css_styles)

# Impor semua modul di awal file
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
except ImportError as e:
    st.error(f"Error importing modules: {str(e)}")
    st.stop()

# Inisialisasi session state
if "subpage" not in st.session_state:
    st.session_state["subpage"] = None

# Halaman Main Page
def main_page():
    st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
    st.title("Selamat Datang!")
    st.write("""
    Aplikasi ini dirancang untuk membantu mempermudah pekerjaan Audit. 
    Di halaman utama ini, Anda akan menemukan informasi dasar dan panduan untuk memulai.
    
    Modul-modul yang tersedia dalam aplikasi ini mencakup:
    - **Depresiasi**: Untuk menghitung nilai penyusutan aset secara cepat dan akurat.
    - **Sample**: Membantu Anda melakukan pengambilan sampel data untuk audit.
    - **Fuzzy Searching**: Mencari data dengan toleransi terhadap kesalahan penulisan.
    - **Query Builder**: Membuat dan mengeksekusi kueri database dengan antarmuka yang mudah.
    - **PDF Tools**: Alat bantu untuk memanipulasi dokumen PDF.
    - **FIFO**: Menghitung persediaan akhir menggunakan metode FIFO (First In, First Out).
    
    Gunakan menu navigasi untuk memilih modul yang sesuai dengan kebutuhan Anda. 
    Semoga aplikasi ini dapat mendukung produktivitas Anda!
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# Halaman Depresiasi
def depresiasi():
    st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
    st.title("Rekalkulasi Penyusutan Aset Tetap")
    st.write("Silahkan pilih metode yang anda inginkan:")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Susut Tahunan"):
            st.session_state["subpage"] = "Susut Tahunan"
    with col2:
        if st.button("Susut Semester"):
            st.session_state["subpage"] = "Susut Semester"
    
    if st.session_state["subpage"] == "Susut Tahunan":
        st.write("### Susut Tahunan")
        try:
            susuttahunan_app()
        except Exception as e:
            st.error(f"Error loading Susut Tahunan: {str(e)}")
    elif st.session_state["subpage"] == "Susut Semester":
        st.write("### Susut Semester")
        try:
            susutsemester_app()
        except Exception as e:
            st.error(f"Error loading Susut Semester: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Halaman Sample
def sample():
    st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
    st.title("Pengambilan Sampel")
    st.write("Silakan pilih metode pengambilan sampel:")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("AHP"):
            st.session_state["subpage"] = "AHP"
    with col2:
        if st.button("MUS"):
            st.session_state["subpage"] = "MUS"
    with col3:
        if st.button("Benford's Law"):
            st.session_state["subpage"] = "Benford's Law"
    
    if st.session_state["subpage"] == "AHP":
        st.write("### Analytic Hierarchy Process (AHP)")
        try:
            ahp_app()
        except Exception as e:
            st.error(f"Error loading AHP: {str(e)}")
    elif st.session_state["subpage"] == "MUS":
        st.write("### Monetary Unit Sampling (MUS)")
        try:
            mus_app()
        except Exception as e:
            st.error(f"Error loading MUS: {str(e)}")
    elif st.session_state["subpage"] == "Benford's Law":
        st.write("### Benford's Law Analysis")
        try:
            benfords_app()
        except Exception as e:
            st.error(f"Error loading Benford's Law: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Halaman PDF Tools
def pdf_tools():
    st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
    st.title("PDF Tools")
    st.write("Silakan pilih alat untuk memanipulasi dokumen PDF:")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Merge PDF"):
            st.session_state["subpage"] = "Merge PDF"
    with col2:
        if st.button("Extract PDF"):
            st.session_state["subpage"] = "Extract PDF"
    
    if st.session_state["subpage"] == "Merge PDF":
        st.write("### Merge PDF")
        try:
            mergepdf_app()
        except Exception as e:
            st.error(f"Error loading Merge PDF: {str(e)}")
    elif st.session_state["subpage"] == "Extract PDF":
        st.write("### Extract PDF")
        try:
            extractpdf_app()
        except Exception as e:
            st.error(f"Error loading Extract PDF: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Halaman FIFO
def fifo():
    st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
    st.title("FIFO Inventory Calculator")
    st.write("Modul FIFO digunakan untuk menghitung persediaan akhir menggunakan metode FIFO (First In, First Out). Silahkan pilih metode yang anda ingin anda gunakan:")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("via input manual"):
            st.session_state["subpage"] = "Individu"
    with col2:
        if st.button("via form excel"):
            st.session_state["subpage"] = "Batch"
    
    if st.session_state["subpage"] == "Individu":
        st.write("### Menggunakan Input Manual")
        try:
            fifoindividu_app()
        except Exception as e:
            st.error(f"Error loading FIFO Individu: {str(e)}")
    elif st.session_state["subpage"] == "Batch":
        st.write("### Menggunakan Form Excel")
        try:
            fifobatch_app()
        except Exception as e:
            st.error(f"Error loading FIFO Batch: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Halaman Fuzzy Searching (Tanpa Subhalaman)
def fuzzy_searching():
    st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
    st.title("Fuzzy Searching")
    try:
        fuzzysearch_app()
    except Exception as e:
        st.error(f"Error loading Fuzzy Search: {str(e)}")
    st.markdown('</div>', unsafe_allow_html=True)

# Halaman Query Builder (Tanpa Subhalaman)
def query_builder():
    st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
    st.title("Query Builder")
    try:
        querybuilder_app()
    except Exception as e:
        st.error(f"Error loading Query Builder: {str(e)}")
    st.markdown('</div>', unsafe_allow_html=True)

# Navigasi halaman utama
page_names_to_funcs = {
    "Main Page": main_page,
    "Depresiasi": depresiasi,
    "Sample": sample,
    "Fuzzy Searching": fuzzy_searching,
    "Query Builder": query_builder,
    "PDF Tools": pdf_tools,
    "FIFO": fifo,
}

# Sidebar Menu Modern dengan Icons
with st.sidebar:
    selected = option_menu(
        menu_title="Main Menu",  # Judul menu
        options=[
            "Main Page",
            "Depresiasi",
            "Sample",
            "Fuzzy Searching",
            "Query Builder",
            "PDF Tools",
            "FIFO",
        ],
        icons=[
            "house",
            "calculator",
            "clipboard-data",
            "search",
            "code-slash",
            "file-earmark-pdf",
            "box",
        ],
        menu_icon="cast",  # Ikon utama
        default_index=0,  # Halaman awal
    )

# Panggil fungsi halaman yang dipilih
try:
    page_names_to_funcs[selected]()
except KeyError:
    st.error("Halaman tidak ditemukan.")

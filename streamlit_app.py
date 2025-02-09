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
/* Konten utama styling */
.main-content {
    padding: 20px;
    background-color: #ffffff;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    text-align: center;
}
.button-container {
    display: flex;
    justify-content: center;
    gap: 10px;
    margin-top: 20px;
}
</style>
"""

# Tambahkan CSS
add_css(css_styles)

# Impor semua modul di awal file
from page.susuttahunan import app as susuttahunan_app
from page.susutsemester import app as susutsemester_app
from page.ahp import app as ahp_app
from page.mus import app as mus_app
from page.benfords import app as benfords_app
from page.fuzzysearch import app as fuzzysearch_app
from page.querybuilder import app as querybuilder_app
from page.mergepdf import app as mergepdf_app
from page.extractpdf import app as extractpdf_app

# Inisialisasi session state
if "subpage" not in st.session_state:
    st.session_state["subpage"] = None

# Halaman Main Page
def main_page():
    st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
    st.title("Main Page")
    st.write("Selamat datang di aplikasi ini!")
    st.markdown('</div>', unsafe_allow_html=True)

# Halaman Depresiasi
def depresiasi():
    st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
    st.title("Depresiasi")
    st.write("Modul Depresiasi digunakan untuk menghitung nilai depresiasi berdasarkan metode yang Anda pilih. Silakan pilih jenis perhitungan:")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Depresiasi Tahunan"):
            st.session_state["subpage"] = "Tahunan"
    with col2:
        if st.button("Depresiasi Semesteran"):
            st.session_state["subpage"] = "Semesteran"
    
    if st.session_state["subpage"] == "Tahunan":
        st.write("### Depresiasi Tahunan")
        susuttahunan_app()
    elif st.session_state["subpage"] == "Semesteran":
        st.write("### Depresiasi Semesteran")
        susutsemester_app()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Halaman Sample
def sample():
    st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
    st.title("Sample")
    st.write("Modul Sample digunakan untuk pengambilan sampel data berdasarkan berbagai metode. Pilih metode yang ingin digunakan:")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("AHP"):
            st.session_state["subpage"] = "AHP"
    with col2:
        if st.button("MUS"):
            st.session_state["subpage"] = "MUS"
    with col3:
        if st.button("Benford Law"):
            st.session_state["subpage"] = "Benford Law"
    
    if st.session_state["subpage"] == "AHP":
        st.write("### Analytic Hierarchy Process (AHP)")
        ahp_app()
    elif st.session_state["subpage"] == "MUS":
        st.write("### Monetary Unit Sampling (MUS)")
        mus_app()
    elif st.session_state["subpage"] == "Benford Law":
        st.write("### Benford Law Analysis")
        benfords_app()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Halaman Fuzzy Searching
def fuzzysearch():
    st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
    st.title("Fuzzy Searching")
    st.write("Halaman untuk pencarian data string menggunakan metode fuzzy search.")
    fuzzysearch_app()
    st.markdown('</div>', unsafe_allow_html=True)

# Halaman Query Builder
def querybuilder():
    st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
    st.title("Query Builder")
    st.write("Halaman untuk membangun query secara dinamis.")
    querybuilder_app()
    st.markdown('</div>', unsafe_allow_html=True)

# Halaman PDF Tools
def pdf():
    st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
    st.title("PDF Tools")
    st.write("Modul PDF Tools memungkinkan Anda untuk mengelola file PDF, seperti menggabungkan atau mengekstrak halaman. Pilih operasi yang ingin dilakukan:")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Merge PDF"):
            st.session_state["subpage"] = "Merge"
    with col2:
        if st.button("Extract PDF"):
            st.session_state["subpage"] = "Extract"
    
    if st.session_state["subpage"] == "Merge":
        st.write("### Merge PDF Files")
        mergepdf_app()
    elif st.session_state["subpage"] == "Extract":
        st.write("### Extract PDF Pages")
        extractpdf_app()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Navigasi halaman utama
page_names_to_funcs = {
    "Main Page": main_page,
    "Depresiasi": depresiasi,
    "Sample": sample,
    "Fuzzy Searching": fuzzysearch,
    "Query Builder": querybuilder,
    "PDF Tools": pdf,
}

# Sidebar untuk navigasi
selected_page = st.sidebar.selectbox("Pilih halaman", page_names_to_funcs.keys())

# Panggil fungsi halaman yang dipilih
page_names_to_funcs[selected_page]()

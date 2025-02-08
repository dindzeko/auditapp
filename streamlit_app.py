import streamlit as st

# Fungsi untuk menambahkan CSS ke aplikasi Streamlit
def add_css(css):
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

# Animasi CSS untuk transisi halaman
css_animation = """
<style>
/* Animasi fade-in */
.fade-in {
    animation: fadeIn 0.5s ease-in-out;
}
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
/* Gaya untuk sidebar */
.sidebar .sidebar-content {
    transition: margin-left 0.3s ease-in-out;
}
</style>
"""
# Tambahkan CSS ke aplikasi
add_css(css_animation)

# Import semua modul di awal file
from page.susuttahunan import app as susuttahunan_app
from page.susutsemester import app as susutsemester_app
from page.ahp import app as ahp_app
from page.mus import app as mus_app
from page.benfords import app as benfords_app
from page.fuzzysearch import app as fuzzysearch_app
from page.querybuilder import app as querybuilder_app
from page.mergepdf import app as mergepdf_app
from page.extractpdf import app as extractpdf_app

# Halaman utama
def main_page():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("Main Page")
    st.write("Welcome")
    st.markdown('</div>', unsafe_allow_html=True)

# Halaman Depresiasi
def depresiasi():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("Depresiasi")
    
    sub_page = st.sidebar.selectbox("Pilih jenis depresiasi", ["Tahunan", "Semesteran"])
    
    if sub_page == "Tahunan":
        susuttahunan_app()
    elif sub_page == "Semesteran":
        susutsemester_app()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Halaman Sample
def sample():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("Sample")
    
    sub_page = st.sidebar.selectbox("Pilih sub-halaman", ["AHP", "MUS", "Benford Law"])
    
    if sub_page == "AHP":
        ahp_app()
    elif sub_page == "MUS":
        mus_app()
    elif sub_page == "Benford Law":
        benfords_app()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Halaman Fuzzy Searching
def fuzzysearch():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("Search")
    st.write("Bentuk Data String")
    fuzzysearch_app()
    st.markdown('</div>', unsafe_allow_html=True)

# Halaman Query Builder
def querybuilder():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("Query Builder")
    st.write("Halaman untuk Query Builder.")
    querybuilder_app()
    st.markdown('</div>', unsafe_allow_html=True)

# Halaman PDF
def pdf():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("PDF Tools")
    
    sub_page = st.sidebar.selectbox("Pilih operasi PDF", ["Merge", "Ekstrak"])
    
    try:
        if sub_page == "Merge":
            mergepdf_app()
        elif sub_page == "Ekstrak":
            extractpdf_app()
    except Exception as e:
        st.error(f"Error: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Navigasi
page_names_to_funcs = {
    "Main Page": main_page,
    "Depresiasi": depresiasi,
    "Sample": sample,
    "Fuzzy Searching": fuzzysearch,
    "Query Builder": querybuilder,
    "PDF Tools": pdf,
}

# Sidebar untuk memilih halaman
selected_page = st.sidebar.selectbox("Pilih halaman", page_names_to_funcs.keys())

# Panggil fungsi halaman yang dipilih
page_names_to_funcs[selected_page]()

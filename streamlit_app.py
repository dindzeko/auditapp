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
        from page.susuttahunan import app as susuttahunan_app
        susuttahunan_app()
    elif sub_page == "Semesteran":
        from page.susutsemester import app as susutsemester_app
        susutsemester_app()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Halaman Sample
def sample():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("Sample")
    
    # Sub-halaman untuk Sample
    sub_page = st.sidebar.selectbox("Pilih sub-halaman", ["AHP", "MUS", "Benford Law"])
    
    # Navigasi antar halaman
    if sub_page == "AHP":
        from page.ahp import app as ahp_app
        ahp_app()
    elif sub_page == "MUS":
        from page.mus import app as mus_app
        mus_app()
    elif sub_page == "Benford Law":
        from page.benfords import app as benfords_app
        benfords_app()
            
    st.markdown('</div>', unsafe_allow_html=True)

# Halaman Fuzzy Searching
def fuzzysearch():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("Search")
    st.write("Bentuk Data String")
    st.markdown('</div>', unsafe_allow_html=True)
    from page.fuzzysearch import app as fuzzysearch_app
    fuzzysearch_app()

# Halaman Query Builder
def querybuilder():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("Query Builder")
    st.write("Halaman untuk Query Builder.")
    st.markdown('</div>', unsafe_allow_html=True)
    from page.querybuilder import app as querybuilder_app
    querybuilder_app()

# Halaman PDF
def pdf():
    st.markdown('<div class="fade-in">', unsafe_allow_html=True)
    st.title("PDF Operations")
    
    # Sub-halaman untuk PDF
    sub_page = st.sidebar.selectbox("Pilih operasi PDF", ["Merge", "Ekstrak"])
    
    # Navigasi antar sub-halaman
    if sub_page == "Merge":
        from page.mergepdf import app as mergepdf_app
        mergepdf_app()
    elif sub_page == "Extract":
        from page.extractpdf import app as extractpdf_app
        extractpdf_app()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Navigasi
page_names_to_funcs = {
    "Main Page": main_page,
    "Depresiasi": depresiasi,
    "Sample": sample,
    "Fuzzy Searching": fuzzysearch,
    "Query Builder": querybuilder,
    "PDF Operations": pdf,  # Menambahkan halaman PDF
}

# Sidebar untuk memilih halaman
selected_page = st.sidebar.selectbox("Pilih halaman", page_names_to_funcs.keys())

# Panggil fungsi halaman yang dipilih
page_names_to_funcs[selected_page]()

import streamlit as st

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

# Fungsi tampilan utama halaman depresiasi
def depresiasi():
    st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
    st.title("Depresiasi")
    st.write("Modul Depresiasi digunakan untuk menghitung nilai depresiasi berdasarkan metode yang Anda pilih. Silakan pilih jenis perhitungan:")
    
    # Tombol untuk subpage
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Depresiasi Tahunan"):
            st.session_state["subpage"] = "Tahunan"
    with col2:
        if st.button("Depresiasi Semesteran"):
            st.session_state["subpage"] = "Semesteran"

    # Tampilkan konten subpage jika dipilih
    if "subpage" in st.session_state:
        if st.session_state["subpage"] == "Tahunan":
            st.write("### Depresiasi Tahunan")
            from page.susuttahunan import app as susuttahunan_app
            susuttahunan_app()
        elif st.session_state["subpage"] == "Semesteran":
            st.write("### Depresiasi Semesteran")
            from page.susutsemester import app as susutsemester_app
            susutsemester_app()
    st.markdown('</div>', unsafe_allow_html=True)

# Fungsi tampilan utama halaman sample
def sample():
    st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
    st.title("Sample")
    st.write("Modul Sample digunakan untuk pengambilan sampel data berdasarkan berbagai metode. Pilih metode yang ingin digunakan:")
    
    # Tombol untuk subpage
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

    # Tampilkan konten subpage jika dipilih
    if "subpage" in st.session_state:
        if st.session_state["subpage"] == "AHP":
            st.write("### Analytic Hierarchy Process (AHP)")
            from page.ahp import app as ahp_app
            ahp_app()
        elif st.session_state["subpage"] == "MUS":
            st.write("### Monetary Unit Sampling (MUS)")
            from page.mus import app as mus_app
            mus_app()
        elif st.session_state["subpage"] == "Benford Law":
            st.write("### Benford Law Analysis")
            from page.benfords import app as benfords_app
            benfords_app()
    st.markdown('</div>', unsafe_allow_html=True)

# Fungsi tampilan utama halaman PDF Tools
def pdf():
    st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
    st.title("PDF Tools")
    st.write("Modul PDF Tools memungkinkan Anda untuk mengelola file PDF, seperti menggabungkan atau mengekstrak halaman. Pilih operasi yang ingin dilakukan:")
    
    # Tombol untuk subpage
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Merge PDF"):
            st.session_state["subpage"] = "Merge"
    with col2:
        if st.button("Extract PDF"):
            st.session_state["subpage"] = "Extract"

    # Tampilkan konten subpage jika dipilih
    if "subpage" in st.session_state:
        if st.session_state["subpage"] == "Merge":
            st.write("### Merge PDF Files")
            from page.mergepdf import app as mergepdf_app
            mergepdf_app()
        elif st.session_state["subpage"] == "Extract":
            st.write("### Extract PDF Pages")
            from page.extractpdf import app as extractpdf_app
            extractpdf_app()
    st.markdown('</div>', unsafe_allow_html=True)

# Navigasi halaman utama
page_names_to_funcs = {
    "Depresiasi": depresiasi,
    "Sample": sample,
    "PDF Tools": pdf,
}

# Sidebar untuk navigasi
selected_page = st.sidebar.selectbox("Pilih halaman", page_names_to_funcs.keys())

# Panggil fungsi halaman yang dipilih
page_names_to_funcs[selected_page]()

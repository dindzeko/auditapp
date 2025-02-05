import streamlit as st

# Fungsi-fungsi halaman
def main_page():
    st.title("Main Page")
    st.write("Ini adalah halaman utama.")

def depresiasi():
    st.title("Depresiasi")
    st.write("Ini adalah halaman Depresiasi.")

def sample():
    st.title("Sample")
    st.write("Ini adalah halaman Sample.")

def vouching():
    st.title("Vouching")
    st.write("Ini adalah halaman Vouching.")

def querybuilder():
    st.title("Query Builder")
    st.write("Ini adalah halaman Query Builder.")

# Daftar halaman
page_names_to_funcs = {
    "Main Page": main_page,
    "Depresiasi": depresiasi,
    "Sample": sample,
    "Vouching": vouching,
    "Query Builder": querybuilder,
}

# Tampilkan tombol-tombol horizontal
cols = st.columns(len(page_names_to_funcs))
for col, (page_name, page_func) in zip(cols, page_names_to_funcs.items()):
    if col.button(page_name):
        # Simpan halaman yang dipilih di session state agar tidak hilang saat refresh
        st.session_state.selected_page = page_name

# Jika ada halaman yang dipilih, tampilkan halaman tersebut
if "selected_page" in st.session_state:
    selected_page = st.session_state.selected_page
    page_names_to_funcs[selected_page]()
else:
    st.write("Silakan pilih halaman.")

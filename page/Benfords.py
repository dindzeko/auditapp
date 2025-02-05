import streamlit as st

# Halaman utama
st.title("Aplikasi Multi-Page")

# Navigasi antar halaman
page = st.sidebar.selectbox("Pilih Halaman", ["Halaman Utama", "Analisis Benford"])

if page == "Halaman Utama":
    st.write("Selamat datang di aplikasi multi-page!")
elif page == "Analisis Benford":
    from pages.benford_analysis import app
    app()

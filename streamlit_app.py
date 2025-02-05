# app.py
import streamlit as st

# Judul aplikasi
st.title("Aplikasi Satuhz")

# Navigasi halaman
menu = ["Home", "Susut Semester", "Susut Tahunan"]
choice = st.sidebar.selectbox("Menu", menu)

if choice == "Home":
    st.header("Selamat Datang di Aplikasi Satuhz")
    st.write("Silakan pilih menu di sidebar untuk melihat fitur-fitur aplikasi.")

elif choice == "Susut Semester":
    # Memuat halaman Susut Semester
    from page.susutsemester import app as susutsemester_app
    susutsemester_app()

elif choice == "Susut Tahunan":
    # Memuat halaman Susut Tahunan
    from page.susuttahunan import app as susuttahunan_app
    susuttahunan_app()

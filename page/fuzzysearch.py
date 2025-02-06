import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz
def (app) 
    # Judul aplikasi
    st.title("Fuzzy Searching"
# Fungsi untuk mencari string dengan toleransi typo
def lookup_with_typo(target, data_list, threshold=80):
    """
    Fungsi untuk mencari string dalam daftar dengan toleransi typo.
    Parameters:
        target (str): String yang ingin dicari.
        data_list (list): Daftar string tempat pencarian dilakukan.
        threshold (int): Ambang batas kemiripan (0-100). Default: 80.
    Returns:
        list of tuples: [(item, score)] untuk setiap item yang melewati threshold.
    """
    results = []
    for item in data_list:
        if isinstance(item, str):  # Pastikan item adalah string
            score = fuzz.ratio(target.lower(), item.lower())  # Hitung kemiripan
            if score >= threshold:
                results.append((item, score))
    return results

# Variabel session state untuk menyimpan data list dan target
if 'data_list' not in st.session_state:
    st.session_state['data_list'] = []

if 'target' not in st.session_state:
    st.session_state['target'] = None

# Judul halaman
st.title("Pencarian dengan Toleransi Typo")

# Bagian Upload Data List
st.subheader("Upload Data List")
uploaded_data_file = st.file_uploader("Pilih file Excel untuk Data List", type=["xlsx", "xls"])

if uploaded_data_file is not None:
    try:
        df = pd.read_excel(uploaded_data_file)
        if 'Data' not in df.columns:
            st.error("File Excel harus memiliki kolom 'Data'.")
        else:
            st.session_state['data_list'] = df['Data'].dropna().tolist()
            st.success(f"Data List berhasil diupload ({len(st.session_state['data_list'])} item).")
    except Exception as e:
        st.error(f"Terjadi kesalahan saat membaca file: {e}")

# Tampilkan Data List jika sudah diupload
if st.session_state['data_list']:
    st.write("Data List yang telah diupload:")
    st.write(st.session_state['data_list'])

# Bagian Upload Target
st.subheader("Upload Target")
uploaded_target_file = st.file_uploader("Pilih file Excel untuk Target", type=["xlsx", "xls"])

if uploaded_target_file is not None:
    try:
        df = pd.read_excel(uploaded_target_file)
        if 'Target' not in df.columns:
            st.error("File Excel harus memiliki kolom 'Target'.")
        else:
            st.session_state['target'] = df['Target'].iloc[0]
            st.success(f"Target berhasil diupload: '{st.session_state['target']}'")
    except Exception as e:
        st.error(f"Terjadi kesalahan saat membaca file: {e}")

# Tampilkan Target jika sudah diupload
if st.session_state['target']:
    st.write("Target yang telah diupload:")
    st.write(st.session_state['target'])

# Bagian Pencarian dan Ekspor
st.subheader("Cari dan Ekspor Hasil")
if st.button("Mulai Pencarian"):
    if not st.session_state['data_list']:
        st.warning("Silakan upload Data List terlebih dahulu.")
    elif not st.session_state['target']:
        st.warning("Silakan upload Target terlebih dahulu.")
    else:
        data_list = st.session_state['data_list']
        target = st.session_state['target']

        # Lakukan pencarian
        results = lookup_with_typo(target, data_list)

        if results:
            result_message = "\n".join([f"{item} (Skor: {score})" for item, score in results])
            st.success(f"String '{target}' ditemukan sebagai kemiripan dengan:\n{result_message}")
        else:
            st.info(f"String '{target}' tidak ditemukan dalam daftar.")

        # Buat DataFrame untuk hasil pencarian
        df = pd.DataFrame(data_list, columns=["Data"])
        df["Target"] = target
        df["Hasil Pencarian"] = df["Data"].apply(
            lambda x: x if any(item == x for item, _ in results) else None
        )
        df["Tingkat/Skor Kemiripan"] = df["Data"].apply(
            lambda x: next((score for item, score in results if item == x), None)
        )

        # Tampilkan hasil dalam tabel
        st.write("Hasil Pencarian:")
        st.dataframe(df)

        # Ekspor ke file Excel
        excel_file = df.to_excel("hasil_pencarian.xlsx", index=False)
        with open("hasil_pencarian.xlsx", "rb") as file:
            st.download_button(
                label="Download Hasil Pencarian",
                data=file,
                file_name="hasil_pencarian.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

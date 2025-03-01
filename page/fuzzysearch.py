import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz

def fuzzy_search_in_target(data_list, target_text, threshold=80):
    """
    Fungsi untuk mencari string dalam teks target dengan toleransi typo.
    Parameters:
        data_list (list): Daftar string (nama) yang ingin dicari.
        target_text (str): Teks target tempat pencarian dilakukan.
        threshold (int): Ambang batas kemiripan (0-100). Default: 80.
    Returns:
        tuple: (hasil_pencarian, skor_kemiripan) atau (None, None) jika tidak ada hasil.
    """
    best_match = None
    best_score = 0
    for item in data_list:
        if isinstance(item, str):  # Pastikan item adalah string
            score = fuzz.ratio(item.lower(), target_text.lower())  # Hitung kemiripan
            if score > best_score and score >= threshold:
                best_match = item
                best_score = score
    return (best_match, best_score) if best_match else (None, None)

def app():
    st.write("Fuzzy Searching merupakan teknik pencocokan data berupa text atau string yang memungkinkan adanya toleransi terhadap ketidaksesuaian kecil dalam teks.")

    # Variabel session state untuk menyimpan data list dan target
    if 'data_list' not in st.session_state:
        st.session_state['data_list'] = []
    if 'target_df' not in st.session_state:
        st.session_state['target_df'] = None

    # Bagian Upload Data List
    st.subheader("Upload Data List")
    uploaded_data_file = st.file_uploader("Upload Excel dengan Nama Kolom Data", type=["xlsx", "xls"])
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
    uploaded_target_file = st.file_uploader("Upload Excel dengan Nama Kolom Target", type=["xlsx", "xls"])
    if uploaded_target_file is not None:
        try:
            df = pd.read_excel(uploaded_target_file)
            if 'Target' not in df.columns:
                st.error("File Excel harus memiliki kolom 'Target'.")
            else:
                st.session_state['target_df'] = df
                st.success(f"Target berhasil diupload ({len(df)} baris).")
        except Exception as e:
            st.error(f"Terjadi kesalahan saat membaca file: {e}")

    # Tampilkan Target jika sudah diupload
    if st.session_state['target_df'] is not None:
        st.write("Target yang telah diupload:")
        st.dataframe(st.session_state['target_df'])

    # Bagian Pencarian dan Ekspor
    st.subheader("Cari dan Ekspor Hasil")
    if st.button("Mulai Pencarian"):
        if not st.session_state['data_list']:
            st.warning("Silakan upload Data List terlebih dahulu.")
        elif st.session_state['target_df'] is None:
            st.warning("Silakan upload Target terlebih dahulu.")
        else:
            data_list = st.session_state['data_list']
            target_df = st.session_state['target_df']

            # Lakukan pencarian fuzzy untuk setiap baris di kolom Target
            results = []
            for _, row in target_df.iterrows():
                target_text = row['Target']
                if isinstance(target_text, str):  # Pastikan target adalah string
                    best_match, best_score = fuzzy_search_in_target(data_list, target_text)
                    results.append((best_match, best_score))
                else:
                    results.append((None, None))

            # Tambahkan hasil pencarian ke DataFrame target
            target_df["Hasil Pencarian"] = [result[0] for result in results]
            target_df["Tingkat Kemiripan"] = [result[1] for result in results]

            # Tampilkan hasil dalam tabel
            st.write("Hasil Pencarian:")
            st.dataframe(target_df)

            # Simpan hasil ke file Excel
            output_filename = "hasil_pencarian.xlsx"
            target_df.to_excel(output_filename, index=False)

            # Unduh hasil
            with open(output_filename, "rb") as file:
                st.download_button(
                    label="Download Hasil Pencarian",
                    data=file,
                    file_name=output_filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

if __name__ == "__main__":
    app()

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

def app():
    # Judul aplikasi
    st.title("Analisis Benford's Law")

    # Penjelasan singkat
    st.write("""
    Aplikasi ini memeriksa apakah data Anda mengikuti distribusi Benford's Law.
    Silakan unggah file Excel (.xlsx), dan aplikasi akan menghitung distribusi angka pertama serta membandingkannya dengan Benford's Law.
    Hasil analisis dapat diekspor ke file Excel.
    """)

    # Fungsi untuk menghitung distribusi Benford
    def calculate_benford_distribution(data):
        # Ekstrak angka pertama (non-nol)
        first_digits = [int(str(abs(num))[0]) for num in data if str(num)[0].isdigit()]
        digit_counts = Counter(first_digits)
        total_count = len(first_digits)
        
        # Hitung frekuensi relatif
        observed_distribution = {digit: count / total_count for digit, count in digit_counts.items()}
        return observed_distribution, total_count

    # Fungsi untuk menghitung distribusi teoretis Benford
    def benford_theoretical():
        return {d: np.log10(1 + 1/d) for d in range(1, 10)}

    # Upload file Excel
    uploaded_file = st.file_uploader("Unggah file Excel (.xlsx)", type=["xlsx"])

    if uploaded_file is not None:
        # Baca file Excel
        df = pd.read_excel(uploaded_file)
        st.write("Pratinjau Data:")
        st.write(df.head())
        
        # Pilih kolom numerik
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        selected_column = st.selectbox("Pilih kolom numerik:", numeric_columns)
        
        if selected_column:
            # Ambil data kolom terpilih
            data = df[selected_column].dropna()
            
            # Hitung distribusi Benford
            observed_distribution, total_count = calculate_benford_distribution(data)
            theoretical_distribution = benford_theoretical()
            
            # Siapkan data untuk ditampilkan
            digits = list(range(1, 10))
            observed_freq = [observed_distribution.get(d, 0) * 100 for d in digits]
            theoretical_freq = [theoretical_distribution[d] * 100 for d in digits]
            
            # Tampilkan hasil dalam tabel
            result_df = pd.DataFrame({
                "Angka Pertama": digits,
                "Frekuensi Observasi (%)": observed_freq,
                "Frekuensi Teoretis (%)": theoretical_freq
            })
            st.write("Hasil Analisis Benford's Law:")
            st.write(result_df)
            
            # Plot grafik
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(digits, observed_freq, color="blue", alpha=0.6, label="Observasi")
            ax.plot(digits, theoretical_freq, color="red", marker="o", label="Teoretis (Benford)")
            ax.set_xlabel("Angka Pertama")
            ax.set_ylabel("Frekuensi (%)")
            ax.set_title("Perbandingan Distribusi Angka Pertama")
            ax.legend()
            st.pyplot(fig)
            
            # Kesimpulan
            st.write(f"Total data yang dianalisis: {total_count}")
            st.write("Jika distribusi observasi mendekati distribusi teoretis, data Anda mungkin mengikuti Benford's Law.")
            
            # Ekspor hasil ke Excel
            st.write("Ekspor Hasil Analisis ke File Excel:")
            if st.button("Ekspor ke Excel"):
                # Simpan hasil ke file Excel
                output_filename = "benford_analysis_result.xlsx"
                result_df.to_excel(output_filename, index=False)
                st.success(f"Hasil analisis berhasil disimpan sebagai '{output_filename}'!")

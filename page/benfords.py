import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter

def app():
    # Judul aplikasi
    st.title("Analisis Benford's Law")
    st.write("""
    Aplikasi ini memeriksa apakah data Anda mengikuti distribusi Benford's Law.
    Silakan unggah file Excel (.xlsx), dan aplikasi akan menghitung distribusi angka pertama serta membandingkannya dengan Benford's Law.
    Hasil analisis dapat diekspor ke file Excel.
    """)
    
    def calculate_benford_distribution(data):
        first_digits = [int(str(abs(num))[0]) for num in data if str(num)[0].isdigit()]
        digit_counts = Counter(first_digits)
        total_count = len(first_digits)
        observed_distribution = {digit: count / total_count for digit, count in digit_counts.items()}
        return observed_distribution, total_count
    
    def benford_theoretical():
        return {d: np.log10(1 + 1/d) for d in range(1, 10)}
    
    uploaded_file = st.file_uploader("Unggah file Excel (.xlsx)", type=["xlsx"])
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        st.write("Pratinjau Data:")
        st.write(df.head())
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        selected_column = st.selectbox("Pilih kolom numerik:", numeric_columns)
        
        if selected_column:
            data = df[selected_column].dropna()
            observed_distribution, total_count = calculate_benford_distribution(data)
            theoretical_distribution = benford_theoretical()
            
            digits = list(range(1, 10))
            observed_freq = [observed_distribution.get(d, 0) * 100 for d in digits]
            theoretical_freq = [theoretical_distribution[d] * 100 for d in digits]
            deviation = [abs(obs - th) for obs, th in zip(observed_freq, theoretical_freq)]
            
            result_df = pd.DataFrame({
                "Angka Pertama": digits,
                "Frekuensi Observasi (%)": observed_freq,
                "Frekuensi Teoretis (%)": theoretical_freq,
                "Deviasi (%)": deviation
            })
            
            # Analisis penyimpangan tertinggi
            max_deviation = max(deviation)
            max_deviation_index = deviation.index(max_deviation)
            digit_max = digits[max_deviation_index]
            
            st.write("Hasil Analisis Benford's Law:")
            st.write(result_df)
            
            # Visualisasi
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.bar(digits, observed_freq, color="blue", alpha=0.6, label="Observasi")
            ax.plot(digits, theoretical_freq, color="red", marker="o", label="Teoretis (Benford)")
            ax.set_xlabel("Angka Pertama")
            ax.set_ylabel("Frekuensi (%)")
            ax.set_title("Perbandingan Distribusi Angka Pertama")
            ax.legend()
            st.pyplot(fig)
            
            # Kesimpulan
            st.subheader("Kesimpulan Analisis")
            st.write(f"""
            - Total data yang dianalisis: **{total_count}**
            - Angka dengan penyimpangan tertinggi: **{digit_max}** (Deviasi: **{max_deviation:.2f}%**)
            - Penyimpangan yang signifikan dari Benford's Law mungkin mengindikasikan anomali atau manipulasi data, 
              namun perlu analisis lebih lanjut untuk konfirmasi.
            """)
            
            # Ekspor ke Excel
            if st.button("Ekspor ke Excel"):
                output_filename = "benford_analysis_result.xlsx"
                result_df.to_excel(output_filename, index=False)
                
                with open(output_filename, "rb") as f:
                    st.download_button(
                        label="Unduh File Excel",
                        data=f,
                        file_name=output_filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                st.success(f"File '{output_filename}' siap diunduh!")

if __name__ == "__main__":
    app()

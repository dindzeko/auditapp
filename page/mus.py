import streamlit as st
import pandas as pd
import random
from io import BytesIO

def app():
    # Judul aplikasi
    st.title("Metode Monetary Unit Sampling (MUS)")

    # Sidebar untuk input parameter
    st.header("Input Parameters")
    total_population = st.number_input("Total Populasi", min_value=1.0, value=1000000.0)
    tolerable_misstatement = st.number_input("Tolerable Misstatement (TM)", min_value=1.0, value=50000.0)
    expected_misstatement = st.number_input("Expected Misstatement (TE)", min_value=0.0, value=10000.0)
    risk_of_incorrect_acceptance = st.selectbox(
        "Risiko Audit (%)",
        options=[10, 5, 2.5],
        index=1  # Default: 5%
    )

    # Faktor Keandalan (Reliability Factor) berdasarkan Risk of Incorrect Acceptance
    reliability_factors = {
        10: 1.5,   # 10% Risk
        5: 1.6,    # 5% Risk
        2.5: 1.9   # 2.5% Risk
    }

    # Expansion Factor berdasarkan Risk of Incorrect Acceptance
    expansion_factors = {
        10: 2.4,   # 10% Risk
        5: 3.0,    # 5% Risk
        2.5: 3.7   # 2.5% Risk
    }

    # Mengambil Reliability Factor dan Expansion Factor berdasarkan Risk of Incorrect Acceptance
    reliability_factor = reliability_factors.get(risk_of_incorrect_acceptance, 1.6)  # Default RF = 1.6
    expansion_factor = expansion_factors.get(risk_of_incorrect_acceptance, 3.0)      # Default EF = 3.0
    st.write(f"Reliability Factor (RF): {reliability_factor}")
    st.write(f"Expansion Factor (EF): {expansion_factor}")

    # Hitung jumlah sampel menggunakan rumus MUS
    if tolerable_misstatement <= (expected_misstatement * expansion_factor):
        st.error("Tolerable Misstatement must be greater than (Expected Misstatement × Expansion Factor).")
        sample_size = None
    else:
        sample_size = int(
            (total_population * reliability_factor) /
            (tolerable_misstatement - (expected_misstatement * expansion_factor))
        )
        st.write(f"Calculated Sample Size: {sample_size}")

    # Upload file populasi
    st.header("Step 1: Upload Daftar Populasi")
    uploaded_population = st.file_uploader("Upload Population Excel File", type=["xlsx"])
    population_df = None
    if uploaded_population:
        try:
            population_df = pd.read_excel(uploaded_population)
            st.success("Population file successfully uploaded!")
            st.write("Preview of Population Data:")
            st.dataframe(population_df.head())

            # Validasi kolom 'Nomor' dan 'Jumlah'
            if 'Nomor' not in population_df.columns or 'Jumlah' not in population_df.columns:
                st.error("The uploaded file must contain columns named 'Nomor' and 'Jumlah'. Please check your file.")
                population_df = None
        except Exception as e:
            st.error(f"Error reading the file: {e}")

    # Generate sample
    st.header("Step 2: Proses Pengambilan Sample")
    if population_df is not None and sample_size is not None:
        # Pilihan untuk menentukan titik awal acak atau manual
        use_random_start = st.checkbox("mau gunakan angka random?", value=True)
        sampling_interval = total_population / sample_size
        if use_random_start:
            # Generate titik awal acak
            random_start = random.uniform(1, sampling_interval)
            st.write(f"Random Starting Point: {random_start:.2f}")
        else:
            # Input manual untuk titik awal
            random_start = st.number_input(
                "Masukkan Nilai Inisiasi",
                min_value=1.0,
                max_value=sampling_interval,
                value=1.0
            )
            st.write(f"Manual Starting Point: {random_start:.2f}")

        if st.button("Generate Sample"):
            try:
                # Pilih sampel berdasarkan interval
                cumulative_value = 0
                selected_samples = []
                for _, row in population_df.iterrows():
                    cumulative_value += row['Jumlah']  # Menggunakan kolom 'Jumlah'
                    while random_start <= cumulative_value:
                        selected_samples.append(row)
                        random_start += sampling_interval

                # Buat DataFrame untuk sampel
                sample_df = pd.DataFrame(selected_samples)

                # Simpan sampel ke session state
                st.session_state.sample_df = sample_df
                st.success("Sample generated successfully!")
                st.write(f"Number of Samples: {len(sample_df)}")
                st.write("Preview of Generated Sample:")
                st.dataframe(sample_df)
            except Exception as e:
                st.error(f"Error generating sample: {e}")

    # Download sample file (Excel format)
    if "sample_df" in st.session_state:
        st.header("Step 3: Download File Sample")

        @st.cache_data
        def convert_df_to_excel(df):
            # Create an in-memory Excel file
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name="Sample")
            return output.getvalue()

        excel_data = convert_df_to_excel(st.session_state.sample_df)
        st.download_button(
            label="Download Sample as Excel",
            data=excel_data,
            file_name="sample.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # Upload filled sample file
    st.header("Step 4: Upload Sample File Pasca Audit")
    uploaded_sample = st.file_uploader("Upload File Sample Untuk Dianalisa", type=["xlsx"])
    sample_filled_df = None
    if uploaded_sample:
        try:
            sample_filled_df = pd.read_excel(uploaded_sample)
            st.success("Filled sample file successfully uploaded!")
            st.write("Preview of Filled Sample Data:")
            st.dataframe(sample_filled_df)

            # Validasi kolom 'Misstatement'
            if 'Misstatement' not in sample_filled_df.columns:
                st.error("The uploaded file must contain a column named 'Misstatement'. Please check your file.")
                sample_filled_df = None
        except Exception as e:
            st.error(f"Error reading the file: {e}")

    # Analyze sample
    st.header("Step 5: Kesimpulan Sample")
    if sample_filled_df is not None:
        if st.button("Analyze Sample"):
            try:
                # Hitung total kesalahan dalam sampel
                total_misstatement = sample_filled_df['Misstatement'].sum()

                # Proyeksi kesalahan ke populasi
                projection_misstatement = total_misstatement * (len(population_df) / len(sample_filled_df))

                # Bandingkan dengan tolerable misstatement
                if projection_misstatement > tolerable_misstatement:
                    result = "Populasi tidak dapat diterima (Material Misstatement)."
                else:
                    result = "Populasi dapat diterima (Tidak ada Material Misstatement)."

                # Tampilkan hasil analisis
                st.write(f"Total Misstatement in Sample: {total_misstatement:.2f}")
                st.write(f"Projection Misstatement: {projection_misstatement:.2f}")
                st.write(f"Tolerable Misstatement: {tolerable_misstatement:.2f}")
                st.write(f"Conclusion: {result}")
                st.success("Analysis complete!")
            except Exception as e:
                st.error(f"Error analyzing sample: {e}")


if __name__ == "__main__":
    app()

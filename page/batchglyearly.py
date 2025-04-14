import streamlit as st
import pandas as pd
from datetime import datetime

# Fungsi Helper: Menghitung Depresiasi
def calculate_depreciation(initial_cost, acquisition_year, useful_life, reporting_year, capitalizations=None, corrections=None):
    if capitalizations is None:
        capitalizations = []
    if corrections is None:
        corrections = []

    # Organize capitalizations and corrections by year
    cap_dict = {}
    for cap in capitalizations:
        year = cap.get('Tahun')  # Use .get() to avoid KeyError
        if year is not None:
            cap_dict.setdefault(year, []).append(cap)

    corr_dict = {}
    for corr in corrections:
        year = corr.get('Tahun')  # Use .get() to avoid KeyError
        if year is not None:
            corr_dict.setdefault(year, []).append(corr)

    # Initialize variables
    book_value = initial_cost
    remaining_life = useful_life
    current_year = acquisition_year
    original_life = useful_life
    accumulated_dep = 0
    schedule = []

    # Calculate yearly depreciation
    while remaining_life > 0 and current_year <= reporting_year:
        # Process capitalizations
        if current_year in cap_dict:
            for cap in cap_dict[current_year]:
                if cap.get('Tahun', float('inf')) > reporting_year:  # Skip if beyond reporting year
                    continue
                book_value += cap.get('Jumlah', 0)  # Default to 0 if 'Jumlah' is missing
                life_extension = cap.get('Tambahan Usia', 0)
                remaining_life = min(remaining_life + life_extension, original_life)

        # Process corrections
        if current_year in corr_dict:
            for corr in corr_dict[current_year]:
                if corr.get('Tahun', float('inf')) > reporting_year:  # Skip if beyond reporting year
                    continue
                book_value -= corr.get('Jumlah', 0)  # Default to 0 if 'Jumlah' is missing

        # Calculate annual depreciation
        annual_dep = book_value / remaining_life if remaining_life > 0 else 0
        accumulated_dep += annual_dep

        # Add to schedule
        schedule.append({
            'year': current_year,
            'depreciation': round(annual_dep, 2),
            'accumulated': round(accumulated_dep, 2),
            'book_value': round(book_value - annual_dep, 2),
            'sisa_mm': remaining_life - 1
        })

        # Update values for next year
        book_value -= annual_dep
        remaining_life -= 1
        current_year += 1

    return schedule


# Fungsi Utama Aplikasi
def app():
    st.title("📉 Depresiasi GL Tahunan")

    # Expander untuk Informasi Batch Tahunan
    with st.expander("📖 Informasi Batch Tahunan ▼", expanded=False):
        st.markdown("""
        ### Fungsi Batch Tahunan
        Subpage **Batch Tahunan** ini dirancang untuk memudahkan pengguna dalam menghitung penyusutan beberapa aset sekaligus tanpa perlu memasukkan data satu per satu secara manual. 
        Untuk menggunakan fitur ini:
        1. Unduh template Excel yang telah disediakan.
        2. Isi data aset tetap (data aset tetap bisa berupa kode barang atau nama barang dengan ketentuan harus unik/tidak boleh sama, histori kapitalisasi, dan histori koreksi kurang aset tetap jika ada sesuai format excel.
        3. Unggah form file Excel yang telah Anda diisi ke aplikasi.
        """)

    # Tombol Unduh Template Excel
    st.subheader("📥 Download Template Excel")
    st.markdown("""
    Silakan unduh template Excel berikut untuk mengisi data aset tetap, kapitalisasi, dan koreksi:
    """)
    if st.button("⬇️ Download Template Excel"):
        st.markdown("""
        [![Download](https://img.shields.io/badge/Download-Template%20Excel-blue)](https://docs.google.com/spreadsheets/d/1b4bueqvZ0vDn7DtKgNK-uVQojLGMM8vQ/edit?usp=drive_link&ouid=106044501644618784207&rtpof=true&sd=true)
        """)

    # Upload Excel File
    uploaded_file = st.file_uploader("📤 Unggah File Excel", type=["xlsx"])
    if uploaded_file is not None:
        try:
            # Read Excel Sheets
            excel_data = pd.ExcelFile(uploaded_file)
            assets_df = excel_data.parse(sheet_name=0)
            capitalizations_df = excel_data.parse(sheet_name=1)
            corrections_df = excel_data.parse(sheet_name=2)

            # Validate Required Columns
            required_columns_assets = {'Nama Aset', 'Harga Perolehan Awal (Rp)', 'Tahun Perolehan', 'Masa Manfaat (tahun)', 'Tahun Pelaporan'}
            required_columns_cap = {'Nama Aset', 'Tahun', 'Jumlah', 'Tambahan Usia'}
            required_columns_corr = {'Nama Aset', 'Tahun', 'Jumlah'}

            if not required_columns_assets.issubset(assets_df.columns):
                st.error("Sheet 1 (Data Aset Tetap) tidak memiliki kolom yang diperlukan.")
                return
            if not required_columns_cap.issubset(capitalizations_df.columns):
                st.error("Sheet 2 (Kapitalisasi) tidak memiliki kolom yang diperlukan.")
                return
            if not required_columns_corr.issubset(corrections_df.columns):
                st.error("Sheet 3 (Koreksi) tidak memiliki kolom yang diperlukan.")
                return

            # Convert Required Columns to Appropriate Data Types
            assets_df['Harga Perolehan Awal (Rp)'] = pd.to_numeric(assets_df['Harga Perolehan Awal (Rp)'], errors='coerce')
            assets_df['Tahun Perolehan'] = pd.to_numeric(assets_df['Tahun Perolehan'], errors='coerce').astype('Int64')
            assets_df['Masa Manfaat (tahun)'] = pd.to_numeric(assets_df['Masa Manfaat (tahun)'], errors='coerce').astype('Int64')
            assets_df['Tahun Pelaporan'] = pd.to_numeric(assets_df['Tahun Pelaporan'], errors='coerce').astype('Int64')

            capitalizations_df['Tahun'] = pd.to_numeric(capitalizations_df['Tahun'], errors='coerce').astype('Int64')
            capitalizations_df['Jumlah'] = pd.to_numeric(capitalizations_df['Jumlah'], errors='coerce').fillna(0)
            capitalizations_df['Tambahan Usia'] = pd.to_numeric(capitalizations_df['Tambahan Usia'], errors='coerce').fillna(0)

            corrections_df['Tahun'] = pd.to_numeric(corrections_df['Tahun'], errors='coerce').astype('Int64')
            corrections_df['Jumlah'] = pd.to_numeric(corrections_df['Jumlah'], errors='coerce').fillna(0)

            # Check for Missing or Invalid Values
            if assets_df.isnull().values.any():
                st.error("Sheet 1 (Data Aset Tetap) mengandung nilai kosong atau tidak valid.")
                return
            if capitalizations_df.isnull().values.any():
                st.error("Sheet 2 (Kapitalisasi) mengandung nilai kosong atau tidak valid.")
                return
            if corrections_df.isnull().values.any():
                st.error("Sheet 3 (Koreksi) mengandung nilai kosong atau tidak valid.")
                return

            # Process Data
            results = []
            schedules = {}
            for _, asset in assets_df.iterrows():
                asset_name = asset['Nama Aset']
                initial_cost = asset['Harga Perolehan Awal (Rp)']
                acquisition_year = asset['Tahun Perolehan']
                useful_life = asset['Masa Manfaat (tahun)']
                reporting_year = asset['Tahun Pelaporan']

                # Filter Capitalizations and Corrections for the Asset
                asset_caps = capitalizations_df[capitalizations_df['Nama Aset'] == asset_name].to_dict(orient='records')
                asset_corrs = corrections_df[corrections_df['Nama Aset'] == asset_name].to_dict(orient='records')

                # Ensure capitalizations and corrections are lists of dictionaries
                if not isinstance(asset_caps, list):
                    asset_caps = []
                if not isinstance(asset_corrs, list):
                    asset_corrs = []

                # Calculate Depreciation
                schedule = calculate_depreciation(
                    initial_cost=initial_cost,
                    acquisition_year=acquisition_year,
                    useful_life=useful_life,
                    reporting_year=reporting_year,
                    capitalizations=asset_caps,
                    corrections=asset_corrs
                )

                # Append Results
                results.append({
                    'Nama Aset': asset_name,
                    'Tahun Pelaporan': reporting_year,
                    'Penyusutan': schedule[-1]['depreciation'],
                    'Akumulasi': schedule[-1]['accumulated'],
                    'Nilai Buku': schedule[-1]['book_value']
                })

                # Save Schedule for Export
                schedules[asset_name] = schedule

            # Display Results
            results_df = pd.DataFrame(results)
            st.subheader("📊 Hasil Penyusutan")
            st.dataframe(results_df.style.format({
                'Penyusutan': lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                'Akumulasi': lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                'Nilai Buku': lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            }), use_container_width=True, hide_index=True)

            # Download Results
            excel_buffer = convert_df_to_excel_with_sheets(results, schedules)
            st.download_button(
                label="📥 Download Hasil",
                data=excel_buffer,
                file_name="hasil_penyusutan.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"❌ Terjadi kesalahan saat memproses file: {str(e)}")


# Jalankan aplikasi
if __name__ == "__main__":
    app()

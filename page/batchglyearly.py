import streamlit as st
import pandas as pd
from datetime import datetime

# Fungsi-fungsi helper
def calculate_depreciation(initial_cost, acquisition_year, useful_life, reporting_year, capitalizations=None, corrections=None):  
    if capitalizations is None:
        capitalizations = []
    if corrections is None:
        corrections = []
    # Organize capitalizations by year
    cap_dict = {}
    for cap in capitalizations:
        year = cap['year']
        cap_dict.setdefault(year, []).append(cap)
    # Organize corrections by year
    corr_dict = {}
    for corr in corrections:
        year = corr['year']
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
                if cap['year'] > reporting_year:
                    continue
                book_value += cap['amount']
                life_extension = cap.get('life_extension', 0)
                remaining_life = min(remaining_life + life_extension, original_life)
        # Process corrections
        if current_year in corr_dict:
            for corr in corr_dict[current_year]:
                if corr['year'] > reporting_year:
                    continue
                book_value -= corr['amount']
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

def convert_df_to_excel_with_sheets(results, schedules):
    import io
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        # Add summary sheet
        results_df = pd.DataFrame(results)
        results_df.to_excel(writer, index=False, sheet_name='Ringkasan')
        
        # Add individual asset sheets
        for asset_name, schedule in schedules.items():
            schedule_df = pd.DataFrame(schedule)
            schedule_df.to_excel(writer, index=False, sheet_name=asset_name[:31])  # Excel sheet name limit is 31 characters
    return buffer.getvalue()

def format_number_indonesia(number):
    if isinstance(number, (int, float)):
        return f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return number

# Fungsi utama aplikasi
def app():
    st.title("📉 Depresiasi GL Tahunan")

    # Upload Excel File
    uploaded_file = st.file_uploader("📤 Unggah File Excel", type=["xlsx"])
    if uploaded_file is not None:
        try:
            # Read Excel Sheets
            excel_data = pd.ExcelFile(uploaded_file)
            assets_df = excel_data.parse(sheet_name=0)
            capitalizations_df = excel_data.parse(sheet_name=1)
            corrections_df = excel_data.parse(sheet_name=2)

            # Validate Data
            required_columns_assets = {'Nama Aset', 'Harga Perolehan Awal (Rp)', 'Tahun Perolehan', 'Masa Manfaat (tahun)', 'Tahun Pelaporan'}
            required_columns_cap = {'Nama Aset', 'Tahun', 'Jumlah', 'Tambahan Usia'}
            required_columns_corr = {'Nama Aset', 'Tahun', 'Jumlah'}

            # Debugging: Print column names
            st.write("Sheet 1 Columns:", assets_df.columns)
            st.write("Sheet 2 Columns:", capitalizations_df.columns)
            st.write("Sheet 3 Columns:", corrections_df.columns)

            # Validate columns
            if not required_columns_assets.issubset(assets_df.columns):
                st.error("Sheet 1 (Data Aset Tetap) tidak memiliki kolom yang diperlukan.")
                return
            if not required_columns_cap.issubset(capitalizations_df.columns):
                st.error("Sheet 2 (Kapitalisasi) tidak memiliki kolom yang diperlukan.")
                return
            if not required_columns_corr.issubset(corrections_df.columns):
                st.error("Sheet 3 (Koreksi) tidak memiliki kolom yang diperlukan.")
                return

            # Convert 'Tahun' columns to integers
            try:
                assets_df['Tahun Perolehan'] = assets_df['Tahun Perolehan'].astype(int)
                assets_df['Masa Manfaat (tahun)'] = assets_df['Masa Manfaat (tahun)'].astype(int)
                assets_df['Tahun Pelaporan'] = assets_df['Tahun Pelaporan'].astype(int)
                capitalizations_df['Tahun'] = capitalizations_df['Tahun'].astype(int)
                corrections_df['Tahun'] = corrections_df['Tahun'].astype(int)
            except ValueError:
                st.error("Kesalahan konversi tipe data pada kolom 'Tahun'. Pastikan semua nilai tahun adalah angka.")
                return

            # Process Data
            results = []
            schedules = {}
            for _, asset in assets_df.iterrows():
                asset_name = asset['Nama Aset']
                initial_cost = asset['Harga Perolehan Awal (Rp)']
                acquisition_year = int(asset['Tahun Perolehan'])
                useful_life = int(asset['Masa Manfaat (tahun)'])
                reporting_year = int(asset['Tahun Pelaporan'])

                # Filter Capitalizations and Corrections for the Asset
                asset_caps = capitalizations_df[capitalizations_df['Nama Aset'] == asset_name].to_dict(orient='records')
                asset_corrs = corrections_df[corrections_df['Nama Aset'] == asset_name].to_dict(orient='records')

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
            st.dataframe(results_df, use_container_width=True, hide_index=True)

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

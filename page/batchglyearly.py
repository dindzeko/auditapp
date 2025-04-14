import streamlit as st
import pandas as pd
from datetime import datetime

# Fungsi Helper: Menghitung Depresiasi
def calculate_depreciation(initial_cost, acquisition_year, useful_life, reporting_year, capitalizations=None, corrections=None):
    """
    Menghitung depresiasi aset berdasarkan parameter yang diberikan.
    """
    if capitalizations is None:
        capitalizations = []
    if corrections is None:
        corrections = []

    # Membuat dictionary untuk kapitalisasi dan koreksi berdasarkan tahun
    cap_dict = {}
    for cap in capitalizations:
        year = cap.get("Tahun")
        if year is not None:
            cap_dict.setdefault(year, []).append(cap)

    corr_dict = {}
    for corr in corrections:
        year = corr.get("Tahun")
        if year is not None:
            corr_dict.setdefault(year, []).append(corr)

    # Inisialisasi variabel utama
    book_value = initial_cost
    remaining_life = useful_life
    current_year = acquisition_year
    accumulated_dep = 0
    schedule = []

    while remaining_life > 0 and current_year <= reporting_year:
        # Proses kapitalisasi pada tahun tertentu
        if current_year in cap_dict:
            for cap in cap_dict[current_year]:
                if cap.get("Tahun", float("inf")) > reporting_year:
                    continue
                book_value += cap.get("Jumlah", 0)
                life_extension = cap.get("Tambahan Usia", 0)
                remaining_life = min(remaining_life + life_extension, useful_life)

        # Proses koreksi pada tahun tertentu
        if current_year in corr_dict:
            for corr in corr_dict[current_year]:
                if corr.get("Tahun", float("inf")) > reporting_year:
                    continue
                book_value -= corr.get("Jumlah", 0)

        # Hitung depresiasi tahunan
        annual_dep = book_value / remaining_life if remaining_life > 0 else 0
        accumulated_dep += annual_dep

        # Simpan hasil perhitungan ke dalam schedule
        schedule.append({
            "year": current_year,
            "depreciation": round(annual_dep, 2),
            "accumulated": round(accumulated_dep, 2),
            "book_value": round(book_value - annual_dep, 2),
            "sisa_mm": remaining_life - 1,
        })

        # Update nilai buku, sisa masa manfaat, dan tahun saat ini
        book_value -= annual_dep
        remaining_life -= 1
        current_year += 1

    return schedule

# Fungsi Helper: Konversi DataFrame ke Excel dengan Multiple Sheets
def convert_df_to_excel_with_sheets(results, schedules):
    """
    Mengonversi hasil perhitungan menjadi file Excel dengan beberapa sheet.
    """
    import io
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        # Sheet Ringkasan
        results_df = pd.DataFrame(results)
        results_df.to_excel(writer, index=False, sheet_name="Ringkasan")

        # Sheet per Aset
        for asset_name, schedule in schedules.items():
            schedule_df = pd.DataFrame(schedule)
            sheet_name = str(asset_name)[:31]  # Nama sheet maksimal 31 karakter
            schedule_df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buffer.getvalue()

# Fungsi Utama Aplikasi
def app():
    st.title("📉 Depresiasi GL Tahunan")

    # Informasi Batch Tahunan
    with st.expander("📖 Informasi Batch Tahunan ▼", expanded=False):
        st.markdown("""
        ### Fungsi Batch Tahunan
        1. Unduh template Excel.
        2. Isi data aset, kapitalisasi, dan koreksi.
        3. Unggah file Excel.
        """)

    # Download Template Excel
    st.subheader("📥 Download Template Excel")
    if st.button("⬇️ Download Template Excel"):
        st.markdown("[Download](https://docs.google.com/spreadsheets/d/1b4bueqvZ0vDn7DtKgNK-uVQojLGMM8vQ/edit?usp=drive_link)")

    # Unggah File Excel
    uploaded_file = st.file_uploader("📤 Unggah File Excel", type=["xlsx"])
    if uploaded_file is not None:
        try:
            excel_data = pd.ExcelFile(uploaded_file)

            # Baca data dari setiap sheet
            assets_df = excel_data.parse(sheet_name=0)
            capitalizations_df = excel_data.parse(sheet_name=1)
            corrections_df = excel_data.parse(sheet_name=2)

            # Validasi kolom dan tipe data
            required_assets = {"Nama Aset", "Harga Perolehan Awal (Rp)", "Tahun Perolehan", "Masa Manfaat (tahun)", "Tahun Pelaporan"}
            if not required_assets.issubset(assets_df.columns):
                st.error("Kolom di Sheet 1 tidak valid!")
                return

            # Konversi tipe data numerik
            numeric_columns = ["Harga Perolehan Awal (Rp)", "Tahun Perolehan", "Masa Manfaat (tahun)", "Tahun Pelaporan"]
            for col in numeric_columns:
                assets_df[col] = pd.to_numeric(assets_df[col], errors="coerce")

            # Proses perhitungan
            results = []
            schedules = {}
            for _, asset in assets_df.iterrows():
                asset_name = str(asset["Nama Aset"])  # Pastikan string
                initial_cost = asset["Harga Perolehan Awal (Rp)"]
                acquisition_year = int(asset["Tahun Perolehan"])
                useful_life = int(asset["Masa Manfaat (tahun)"])
                reporting_year = int(asset["Tahun Pelaporan"])

                # Filter data kapitalisasi dan koreksi
                asset_caps = capitalizations_df[capitalizations_df["Nama Aset"] == asset_name].to_dict("records")
                asset_corrs = corrections_df[corrections_df["Nama Aset"] == asset_name].to_dict("records")

                # Hitung depresiasi
                schedule = calculate_depreciation(
                    initial_cost, acquisition_year, useful_life, reporting_year, asset_caps, asset_corrs
                )

                # Simpan hasil perhitungan
                results.append({
                    "Nama Aset": asset_name,
                    "Tahun Pelaporan": reporting_year,
                    "Penyusutan": schedule[-1]["depreciation"] if schedule else 0,
                    "Akumulasi": schedule[-1]["accumulated"] if schedule else 0,
                    "Nilai Buku": schedule[-1]["book_value"] if schedule else 0,
                })
                schedules[asset_name] = schedule

            # Tampilkan hasil
            results_df = pd.DataFrame(results)
            st.dataframe(results_df.style.format({
                "Penyusutan": "{:,.2f}".format,
                "Akumulasi": "{:,.2f}".format,
                "Nilai Buku": "{:,.2f}".format,
            }))

            # Download hasil
            excel_buffer = convert_df_to_excel_with_sheets(results, schedules)
            st.download_button(
                "📥 Download Hasil",
                excel_buffer,
                "hasil_penyusutan.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    app()

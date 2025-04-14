import streamlit as st
import pandas as pd
from datetime import datetime

# Fungsi Helper: Menghitung Depresiasi (Versi Diperbaiki)
def calculate_depreciation(initial_cost, acquisition_year, useful_life, reporting_year, capitalizations=None, corrections=None):
    if capitalizations is None:
        capitalizations = []
    if corrections is None:
        corrections = []

    # Organisasi data berdasarkan tahun
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

    # Inisialisasi variabel
    book_value = initial_cost
    remaining_life = useful_life
    current_year = acquisition_year
    accumulated_dep = 0
    schedule = []

    # Proses per tahun hingga tahun pelaporan
    while current_year <= reporting_year:
        # Proses kapitalisasi di awal tahun
        if current_year in cap_dict:
            for cap in cap_dict[current_year]:
                # Jika aset sudah habis, perlakukan sebagai aset baru
                if remaining_life <= 0:
                    book_value = cap.get("Jumlah", 0)
                    remaining_life = cap.get("Tambahan Usia", 0)
                else:
                    book_value += cap.get("Jumlah", 0)
                    tambahan_usia = cap.get("Tambahan Usia", 0)
                    remaining_life = min(
                        remaining_life + tambahan_usia,
                        useful_life + tambahan_usia
                    )

        # Proses koreksi di awal tahun
        if current_year in corr_dict:
            for corr in corr_dict[current_year]:
                book_value -= corr.get("Jumlah", 0)

        # Hitung penyusutan hanya jika masa manfaat tersisa
        annual_dep = 0
        if remaining_life > 0:
            annual_dep = book_value / remaining_life
            accumulated_dep += annual_dep
            book_value -= annual_dep
            remaining_life -= 1

        # Catat semua tahun meski tanpa penyusutan
        schedule.append({
            "year": current_year,
            "depreciation": round(annual_dep, 2),
            "accumulated": round(accumulated_dep, 2),
            "book_value": round(book_value, 2),
            "sisa_mm": remaining_life,
        })

        current_year += 1

    return schedule

# Fungsi Helper: Konversi DataFrame ke Excel dengan Multiple Sheets
def convert_df_to_excel_with_sheets(results, schedules):
    import io
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        # Sheet Ringkasan
        results_df = pd.DataFrame(results)
        results_df.to_excel(writer, index=False, sheet_name="Ringkasan")
        
        # Sheet per Aset
        for asset_name, schedule in schedules.items():
            schedule_df = pd.DataFrame(schedule)
            sheet_name = str(asset_name)[:31]
            schedule_df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buffer.getvalue()

# Fungsi Utama Aplikasi
def app():
    st.title("📉 Depresiasi GL Tahunan (Versi Diperbaiki)")

    with st.expander("📖 Informasi Batch Tahunan ▼", expanded=False):
        st.markdown("""
        ### Perbaikan Utama:
        1. **Penanganan kapitalisasi setelah masa manfaat habis**  
           - Diperlakukan sebagai aset baru
        2. **Pencatatan semua tahun**  
           - Termasuk tahun tanpa penyusutan
        3. **Perhitungan masa manfaat dinamis**  
           - Ekstensi masa manfaat dihitung dengan benar
        """)

    st.subheader("📥 Download Template Excel")
    if st.button("⬇️ Download Template Excel"):
        st.markdown("[Download Template](https://docs.google.com/spreadsheets/d/1b4bueqvZ0vDn7DtKgNK-uVQojLGMM8vQ/edit?usp=drive_link)")

    uploaded_file = st.file_uploader("📤 Unggah File Excel", type=["xlsx"])
    if uploaded_file is not None:
        try:
            excel_data = pd.ExcelFile(uploaded_file)
            
            # Baca dan proses data
            assets_df = excel_data.parse(sheet_name=0)
            capitalizations_df = excel_data.parse(sheet_name=1)
            corrections_df = excel_data.parse(sheet_name=2)

            # Validasi data
            required_columns = ["Nama Aset", "Harga Perolehan Awal (Rp)", "Tahun Perolehan", 
                              "Masa Manfaat (tahun)", "Tahun Pelaporan"]
            if not all(col in assets_df.columns for col in required_columns):
                st.error("Format kolom tidak valid di sheet Aset!")
                return

            # Proses perhitungan
            results = []
            schedules = {}
            for _, asset in assets_df.iterrows():
                asset_name = str(asset["Nama Aset"])
                initial_cost = asset["Harga Perolehan Awal (Rp)"]
                acquisition_year = int(asset["Tahun Perolehan"])
                useful_life = int(asset["Masa Manfaat (tahun)"])
                reporting_year = int(asset["Tahun Pelaporan"])

                # Filter data terkait aset
                asset_caps = capitalizations_df[
                    capitalizations_df["Nama Aset"] == asset_name
                ].to_dict("records")
                
                asset_corrs = corrections_df[
                    corrections_df["Nama Aset"] == asset_name
                ].to_dict("records")

                # Hitung penyusutan
                schedule = calculate_depreciation(
                    initial_cost, acquisition_year, useful_life, 
                    reporting_year, asset_caps, asset_corrs
                )

                # Simpan hasil
                last_entry = schedule[-1] if schedule else {}
                results.append({
                    "Nama Aset": asset_name,
                    "Tahun Pelaporan": reporting_year,
                    "Penyusutan": last_entry.get("depreciation", 0),
                    "Akumulasi": last_entry.get("accumulated", 0),
                    "Nilai Buku": last_entry.get("book_value", 0),
                })
                schedules[asset_name] = schedule

            # Tampilkan hasil
            st.subheader("📊 Hasil Perhitungan")
            results_df = pd.DataFrame(results)
            st.dataframe(results_df.style.format({
                "Penyusutan": "{:,.2f}",
                "Akumulasi": "{:,.2f}",
                "Nilai Buku": "{:,.2f}",
            }))

            # Download hasil
            excel_buffer = convert_df_to_excel_with_sheets(results, schedules)
            st.download_button(
                "💾 Download Full Report (Excel)",
                excel_buffer,
                "laporan_penyusutan.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"❌ Kesalahan: {str(e)}")

if __name__ == "__main__":
    app()

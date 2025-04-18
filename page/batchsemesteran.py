import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO

# Fungsi Helper: Konversi Tanggal ke Semester
def convert_date_to_semester(date_str):
    try:
        date = datetime.strptime(date_str, "%m/%d/%Y")
    except ValueError:
        try:
            date = datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            raise ValueError(f"Tanggal tidak valid: {date_str}")
    year = date.year
    month = date.month
    semester = 1 if 1 <= month <= 6 else 2
    return (year, semester)

# Fungsi Helper: Menghitung Depresiasi Semesteran
def calculate_depreciation(initial_cost, acquisition_date, useful_life, reporting_date, capitalizations=None, corrections=None):
    if capitalizations is None:
        capitalizations = []
    if corrections is None:
        corrections = []

    useful_life_semesters = useful_life * 2
    original_life_semesters = useful_life_semesters

    acquisition_year, acquisition_semester = convert_date_to_semester(acquisition_date)
    reporting_year, reporting_semester = convert_date_to_semester(reporting_date)

    cap_dict = {}
    for cap in capitalizations:
        key = convert_date_to_semester(cap["Tanggal"])
        cap_dict.setdefault(key, []).append(cap)

    corr_dict = {}
    for corr in corrections:
        key = convert_date_to_semester(corr["Tanggal"])
        corr_dict.setdefault(key, []).append(corr)

    book_value = initial_cost
    remaining_life = useful_life_semesters
    current_year, current_semester = acquisition_year, acquisition_semester
    accumulated_dep = 0
    schedule = []

    while (current_year < reporting_year) or (current_year == reporting_year and current_semester <= reporting_semester):
        key = (current_year, current_semester)
        if key in cap_dict:
            for cap in cap_dict[key]:
                book_value += cap.get("Jumlah", 0)
                life_extension = cap.get("Tambahan Usia", 0) * 2
                remaining_life = min(remaining_life + life_extension, original_life_semesters)

        if key in corr_dict:
            for corr in corr_dict[key]:
                book_value = max(book_value - corr.get("Jumlah", 0), 0)

        semester_dep = 0
        if remaining_life > 0:
            semester_dep = book_value / remaining_life
            accumulated_dep += semester_dep
            book_value -= semester_dep
            remaining_life -= 1

        schedule.append({
            "year": current_year,
            "semester": current_semester,
            "depreciation": round(semester_dep, 2),
            "accumulated": round(accumulated_dep, 2),
            "book_value": round(book_value, 2),
            "sisa_mm": remaining_life,
        })

        if current_semester == 1:
            current_semester = 2
        else:
            current_semester = 1
            current_year += 1

    return schedule

def convert_df_to_excel_with_sheets(results, schedules):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    results_df = pd.DataFrame(results)
    results_df.to_excel(writer, sheet_name="Hasil Ringkasan", index=False)
    for asset_name, schedule in schedules.items():
        schedule_df = pd.DataFrame(schedule)
        schedule_df.to_excel(writer, sheet_name=asset_name[:31], index=False)
    writer.close()
    output.seek(0)
    return output

def app():
    st.title("📉 Depresiasi GL Semesteran")

    with st.expander("📖 Informasi Batch Semesteran ▼", expanded=False):
        st.markdown("""
        ### Fungsi Batch Semesteran
        1. Unduh template Excel.
        2. Isi data aset, kapitalisasi, dan koreksi menggunakan **Tanggal** (DD/MM/YYYY).
        3. Unggah file Excel.
        """)

    st.subheader("📥 Download Template Excel")
    if st.button("⬇️ Download Template Excel"):
        st.markdown("[Download](https://docs.google.com/spreadsheets/d/1b4bueqvZ0vDn7DtKgNK-uVQojLGMM8vQ/edit?usp=drive_link)")

    uploaded_file = st.file_uploader("📤 Unggah File Excel", type=["xlsx"])
    if uploaded_file is not None:
        try:
            excel_data = pd.ExcelFile(uploaded_file)
            
            # Baca data dan proses rename kolom terlebih dahulu
            assets_df = excel_data.parse(sheet_name=0)
            assets_df.rename(columns={
                "Tahun Perolehan": "Tanggal Perolehan",
                "Tahun Pelaporan": "Tanggal Pelaporan"
            }, inplace=True)
            
            # Validasi kolom setelah rename
            required_assets = {
                "Nama Aset", 
                "Harga Perolehan Awal (Rp)", 
                "Tanggal Perolehan", 
                "Masa Manfaat (tahun)", 
                "Tanggal Pelaporan"
            }
            if not required_assets.issubset(assets_df.columns):
                st.error("Kolom di Sheet 1 tidak valid! Pastikan kolom sesuai template.")
                return

            # Proses data lainnya
            capitalizations_df = excel_data.parse(sheet_name=1)
            corrections_df = excel_data.parse(sheet_name=2)
            
            # Konversi tipe data
            assets_df["Harga Perolehan Awal (Rp)"] = pd.to_numeric(assets_df["Harga Perolehan Awal (Rp)"], errors="coerce")
            assets_df["Masa Manfaat (tahun)"] = pd.to_numeric(assets_df["Masa Manfaat (tahun)"], errors="coerce")
            
            # Konversi tanggal
            assets_df["Tanggal Perolehan"] = assets_df["Tanggal Perolehan"].apply(
                lambda x: datetime.strptime(x, "%m/%d/%Y").strftime("%d/%m/%Y") if isinstance(x, str) else x.strftime("%d/%m/%Y")
            )
            assets_df["Tanggal Pelaporan"] = assets_df["Tanggal Pelaporan"].apply(
                lambda x: datetime.strptime(x, "%m/%d/%Y").strftime("%d/%m/%Y") if isinstance(x, str) else x.strftime("%d/%m/%Y")
            )

            results = []
            schedules = {}
            for _, asset in assets_df.iterrows():
                asset_name = str(asset["Nama Aset"])
                initial_cost = asset["Harga Perolehan Awal (Rp)"]
                acquisition_date = asset["Tanggal Perolehan"]
                useful_life = int(asset["Masa Manfaat (tahun)"])
                reporting_date = asset["Tanggal Pelaporan"]

                asset_caps = capitalizations_df[capitalizations_df["Nama Aset"] == asset_name].to_dict("records")
                asset_corrs = corrections_df[corrections_df["Nama Aset"] == asset_name].to_dict("records")

                schedule = calculate_depreciation(
                    initial_cost, acquisition_date, useful_life, reporting_date, asset_caps, asset_corrs
                )

                results.append({
                    "Nama Aset": asset_name,
                    "Tanggal Pelaporan": reporting_date,
                    "Penyusutan": schedule[-1]["depreciation"] if schedule else 0,
                    "Akumulasi": schedule[-1]["accumulated"] if schedule else 0,
                    "Nilai Buku": schedule[-1]["book_value"] if schedule else 0,
                })
                schedules[asset_name] = schedule

            results_df = pd.DataFrame(results)
            st.dataframe(results_df.style.format({
                "Penyusutan": "{:,.2f}".format,
                "Akumulasi": "{:,.2f}".format,
                "Nilai Buku": "{:,.2f}".format,
            }))

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

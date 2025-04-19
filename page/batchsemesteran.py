import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
import requests

# Fungsi Helper: Konversi Tanggal ke Semester
def convert_date_to_semester(date_str):
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

# Fungsi Helper: Memastikan Format Tanggal
def ensure_date_format(date_value):
    if isinstance(date_value, pd.Timestamp):
        return date_value.strftime("%d/%m/%Y")
    elif isinstance(date_value, str):
        try:
            parsed_date = datetime.strptime(date_value, "%m/%d/%y")
            return parsed_date.strftime("%d/%m/%Y")
        except ValueError:
            try:
                parsed_date = datetime.strptime(date_value, "%d/%m/%Y")
                return parsed_date.strftime("%d/%m/%Y")
            except ValueError:
                raise ValueError(f"Format tanggal tidak valid: {date_value}")
    else:
        raise ValueError(f"Tipe data tanggal tidak valid: {type(date_value)}")

# Fungsi konversi angka Indonesia ke float
def convert_indonesian_number(number_str):
    if isinstance(number_str, (int, float)):
        return float(number_str)
    return float(
        str(number_str)
        .replace(".", "")  # Hapus pemisah ribuan
        .replace(",", ".")  # Ganti desimal koma dengan titik
    )

# Fungsi Helper: Konversi DataFrame ke Excel dengan Beberapa Sheet
def convert_df_to_excel_with_sheets(results, schedules):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    # Menulis sheet Hasil Ringkasan
    results_df = pd.DataFrame(results)
    results_df.to_excel(writer, sheet_name="Hasil Ringkasan", index=False)
    # Menulis sheet untuk setiap aset
    for asset_name, schedule in schedules.items():
        schedule_df = pd.DataFrame(schedule)
        # Pastikan nama sheet valid (maksimal 31 karakter, tanpa karakter khusus)
        valid_sheet_name = str(asset_name)[:31].replace("/", "_").replace(":", "_")
        # Buat worksheet baru untuk aset tertentu
        worksheet = writer.book.add_worksheet(valid_sheet_name)
        # Tulis DataFrame jadwal depresiasi ke worksheet mulai dari baris kedua
        schedule_df.to_excel(writer, sheet_name=valid_sheet_name, startrow=1, index=False)
        # Tambahkan baris tambahan di awal
        worksheet.write(0, 0, "Nama Aset")  # Kolom A1
        worksheet.write(0, 1, asset_name)   # Kolom B1
    writer.close()
    output.seek(0)
    return output

# Fungsi untuk mengunduh template Excel
def download_template():
    file_url = "https://drive.google.com/uc?export=download&id=1U5EUhvqeQfOPtBDqZNB8P1q-wvdQakPZ"
    response = requests.get(file_url)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception("Gagal mengunduh template Excel.")

# Aplikasi Utama
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
        try:
            template_content = download_template()
            st.download_button(
                label="⬇️ Download Template Excel",
                data=template_content,
                file_name="template_excel.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"❌ Gagal mengunduh template: {str(e)}")

    uploaded_file = st.file_uploader("📤 Unggah File Excel", type=["xlsx"])
    if uploaded_file is not None:
        try:
            excel_data = pd.ExcelFile(uploaded_file)
            # Baca data dan proses rename kolom
            assets_df = excel_data.parse(sheet_name=0)
            assets_df.rename(columns={
                "TANGGAL PEROLEHAN": "Tanggal Perolehan",
                "Tahun Pelaporan": "Tanggal Pelaporan"
            }, inplace=True)
            # Validasi kolom
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
            # Proses data numerik dengan format Indonesia
            assets_df["Harga Perolehan Awal (Rp)"] = assets_df["Harga Perolehan Awal (Rp)"].apply(convert_indonesian_number)
            assets_df["Masa Manfaat (tahun)"] = pd.to_numeric(assets_df["Masa Manfaat (tahun)"], errors="coerce")
            # Konversi tanggal
            assets_df["Tanggal Perolehan"] = assets_df["Tanggal Perolehan"].apply(ensure_date_format)
            assets_df["Tanggal Pelaporan"] = assets_df["Tanggal Pelaporan"].apply(ensure_date_format)
            # Pastikan kolom "Nama Aset" selalu string
            assets_df["Nama Aset"] = assets_df["Nama Aset"].astype(str)
            # Proses sheet kapitalisasi
            capitalizations_df = excel_data.parse(sheet_name=1)
            capitalizations_df.rename(columns={"Tahun": "Tanggal"}, inplace=True)
            capitalizations_df["Tanggal"] = capitalizations_df["Tanggal"].apply(ensure_date_format)
            capitalizations_df["Jumlah"] = capitalizations_df["Jumlah"].apply(convert_indonesian_number)
            capitalizations_df["Nama Aset"] = capitalizations_df["Nama Aset"].astype(str)
            # Proses sheet koreksi
            corrections_df = excel_data.parse(sheet_name=2)
            corrections_df.rename(columns={"Tahun": "Tanggal"}, inplace=True)
            corrections_df["Tanggal"] = corrections_df["Tanggal"].apply(ensure_date_format)
            corrections_df["Jumlah"] = corrections_df["Jumlah"].apply(convert_indonesian_number)
            corrections_df["Nama Aset"] = corrections_df["Nama Aset"].astype(str)
            results = []
            schedules = {}
            for _, asset in assets_df.iterrows():
                asset_name = str(asset["Nama Aset"])  # Pastikan string
                initial_cost = asset["Harga Perolehan Awal (Rp)"]
                acquisition_date = asset["Tanggal Perolehan"]
                useful_life = int(asset["Masa Manfaat (tahun)"])
                reporting_date = asset["Tanggal Pelaporan"]
                # Filter kapitalisasi dan koreksi berdasarkan nama aset
                asset_caps = capitalizations_df[capitalizations_df["Nama Aset"] == asset_name].to_dict("records")
                asset_corrs = corrections_df[corrections_df["Nama Aset"] == asset_name].to_dict("records")
                schedule = calculate_depreciation(
                    initial_cost, acquisition_date, useful_life, reporting_date, asset_caps, asset_corrs
                )
                # Hitung total penyusutan untuk tahun pelaporan (semester I + semester II)
                reporting_year, _ = convert_date_to_semester(reporting_date)
                depreciation_in_reporting_year = sum(
                    entry["depreciation"] for entry in schedule
                    if entry["year"] == reporting_year
                )
                results.append({
                    "Nama Aset": asset_name,
                    "Tanggal Pelaporan": reporting_date,
                    "Penyusutan": round(depreciation_in_reporting_year, 2),
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

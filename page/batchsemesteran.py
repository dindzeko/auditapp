# Fungsi Helper: Konversi Tanggal ke Semester
def convert_date_to_semester(date_str):
    """
    Mengonversi tanggal menjadi (Tahun, Semester).
    Contoh:
        "01/03/2023" -> (2023, 1)  # Semester 1
        "15/09/2023" -> (2023, 2)  # Semester 2
    """
    date = datetime.strptime(date_str, "%d/%m/%Y")  # Format tanggal: DD/MM/YYYY
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

    # Konversi masa manfaat dari tahun ke semester
    useful_life_semesters = useful_life * 2
    original_life_semesters = useful_life_semesters  # Simpan masa manfaat awal dalam semester

    # Konversi tanggal perolehan dan pelaporan ke (Tahun, Semester)
    acquisition_year, acquisition_semester = convert_date_to_semester(acquisition_date)
    reporting_year, reporting_semester = convert_date_to_semester(reporting_date)

    # Organize capitalizations and corrections by semester
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
        # Proses kapitalisasi
        key = (current_year, current_semester)
        if key in cap_dict:
            for cap in cap_dict[key]:
                # Update nilai buku
                book_value += cap.get("Jumlah", 0)
                
                # Update masa manfaat dengan batasan tidak melebihi masa manfaat awal
                life_extension = cap.get("Tambahan Usia", 0) * 2  # Konversi tahun ke semester
                remaining_life = min(remaining_life + life_extension, original_life_semesters)

        # Proses koreksi
        if key in corr_dict:
            for corr in corr_dict[key]:
                book_value = max(book_value - corr.get("Jumlah", 0), 0)  # Minimal 0

        # Hitung penyusutan hanya jika ada sisa masa manfaat
        semester_dep = 0
        if remaining_life > 0:
            semester_dep = book_value / remaining_life
            accumulated_dep += semester_dep
            book_value -= semester_dep
            remaining_life -= 1

        # Catat ke schedule
        schedule.append({
            "year": current_year,
            "semester": current_semester,
            "depreciation": round(semester_dep, 2),
            "accumulated": round(accumulated_dep, 2),
            "book_value": round(book_value, 2),
            "sisa_mm": remaining_life,
        })

        # Debugging (opsional)
        print(f"Year: {current_year}, Semester: {current_semester}, Book Value: {book_value}, Remaining Life: {remaining_life}, Semester Depreciation: {semester_dep}")

        # Pindah ke semester berikutnya
        if current_semester == 1:
            current_semester = 2
        else:
            current_semester = 1
            current_year += 1

    return schedule

# Fungsi Utama Aplikasi
def batchsemesteran_app():
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
            
            # Baca dan konversi kolom "Nama Aset" ke string
            assets_df = excel_data.parse(sheet_name=0)
            capitalizations_df = excel_data.parse(sheet_name=1)
            corrections_df = excel_data.parse(sheet_name=2)
            
            assets_df["Nama Aset"] = assets_df["Nama Aset"].astype(str)
            capitalizations_df["Nama Aset"] = capitalizations_df["Nama Aset"].astype(str)
            corrections_df["Nama Aset"] = corrections_df["Nama Aset"].astype(str)

            # Validasi kolom dan tipe data
            required_assets = {"Nama Aset", "Harga Perolehan Awal (Rp)", "Tanggal Perolehan", "Masa Manfaat (tahun)", "Tanggal Pelaporan"}
            if not required_assets.issubset(assets_df.columns):
                st.error("Kolom di Sheet 1 tidak valid!")
                return

            # Konversi tipe data numerik
            numeric_columns = ["Harga Perolehan Awal (Rp)", "Masa Manfaat (tahun)"]
            for col in numeric_columns:
                assets_df[col] = pd.to_numeric(assets_df[col], errors="coerce")
            
            # Konversi kolom tanggal
            assets_df["Tanggal Perolehan"] = assets_df["Tanggal Perolehan"].astype(str)
            assets_df["Tanggal Pelaporan"] = assets_df["Tanggal Pelaporan"].astype(str)

            # Proses perhitungan
            results = []
            schedules = {}
            for _, asset in assets_df.iterrows():
                asset_name = str(asset["Nama Aset"])  # Pastikan string
                initial_cost = asset["Harga Perolehan Awal (Rp)"]
                acquisition_date = asset["Tanggal Perolehan"]
                useful_life = int(asset["Masa Manfaat (tahun)"])
                reporting_date = asset["Tanggal Pelaporan"]

                # Filter data kapitalisasi dan koreksi
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

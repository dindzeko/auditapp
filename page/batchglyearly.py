import streamlit as st
import pandas as pd
from datetime import datetime

def calculate_depreciation(initial_cost, acquisition_year, useful_life, reporting_year, capitalizations=None, corrections=None):
    if capitalizations is None:
        capitalizations = []
    if corrections is None:
        corrections = []

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

    book_value = initial_cost
    remaining_life = useful_life
    current_year = acquisition_year
    accumulated_dep = 0
    schedule = []

    while current_year <= reporting_year:
        # Proses kapitalisasi untuk tahun ini
        if current_year in cap_dict:
            for cap in cap_dict[current_year]:
                if cap.get("Tahun", float("inf")) > reporting_year:
                    continue
                book_value += cap.get("Jumlah", 0)
                life_extension = cap.get("Tambahan Usia", 0)
                remaining_life += life_extension  # Tambahkan masa manfaat tanpa batas

        # Proses koreksi untuk tahun ini
        if current_year in corr_dict:
            for corr in corr_dict[current_year]:
                if corr.get("Tahun", float("inf")) > reporting_year:
                    continue
                book_value -= corr.get("Jumlah", 0)

        # Hitung penyusutan hanya jika masa manfaat tersisa
        annual_dep = 0
        if remaining_life > 0:
            annual_dep = book_value / remaining_life
            accumulated_dep += annual_dep
            book_value -= annual_dep
            remaining_life -= 1

        # Catat ke jadwal
        schedule.append({
            "year": current_year,
            "depreciation": round(annual_dep, 2),
            "accumulated": round(accumulated_dep, 2),
            "book_value": round(book_value, 2),
            "sisa_mm": remaining_life,
        })

        current_year += 1

    return schedule

def convert_df_to_excel_with_sheets(results, schedules):
    import io
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        results_df = pd.DataFrame(results)
        results_df.to_excel(writer, index=False, sheet_name="Ringkasan")
        for asset_name, schedule in schedules.items():
            schedule_df = pd.DataFrame(schedule)
            sheet_name = str(asset_name)[:31]
            schedule_df.to_excel(writer, index=False, sheet_name=sheet_name)
    return buffer.getvalue()

def app():
    st.title("📉 Depresiasi GL Tahunan")

    with st.expander("📖 Informasi Batch Tahunan ▼", expanded=False):
        st.markdown("""
        ### Fungsi Batch Tahunan
        1. Unduh template Excel.
        2. Isi data aset, kapitalisasi, dan koreksi.
        3. Unggah file Excel.
        """)

    st.subheader("📥 Download Template Excel")
    if st.button("⬇️ Download Template Excel"):
        st.markdown("[Download](https://docs.google.com/spreadsheets/d/1b4bueqvZ0vDn7DtKgNK-uVQojLGMM8vQ/edit?usp=drive_link)")

    uploaded_file = st.file_uploader("📤 Unggah File Excel", type=["xlsx"])
    if uploaded_file is not None:
        try:
            excel_data = pd.ExcelFile(uploaded_file)
            assets_df = excel_data.parse(sheet_name=0)
            capitalizations_df = excel_data.parse(sheet_name=1)
            corrections_df = excel_data.parse(sheet_name=2)
            
            assets_df["Nama Aset"] = assets_df["Nama Aset"].astype(str)
            capitalizations_df["Nama Aset"] = capitalizations_df["Nama Aset"].astype(str)
            corrections_df["Nama Aset"] = corrections_df["Nama Aset"].astype(str)

            required_assets = {"Nama Aset", "Harga Perolehan Awal (Rp)", "Tahun Perolehan", "Masa Manfaat (tahun)", "Tahun Pelaporan"}
            if not required_assets.issubset(assets_df.columns):
                st.error("Kolom di Sheet 1 tidak valid!")
                return

            numeric_columns = ["Harga Perolehan Awal (Rp)", "Tahun Perolehan", "Masa Manfaat (tahun)", "Tahun Pelaporan"]
            for col in numeric_columns:
                assets_df[col] = pd.to_numeric(assets_df[col], errors="coerce")
            
            results = []
            schedules = {}
            for _, asset in assets_df.iterrows():
                asset_name = str(asset["Nama Aset"])
                initial_cost = asset["Harga Perolehan Awal (Rp)"]
                acquisition_year = int(asset["Tahun Perolehan"])
                useful_life = int(asset["Masa Manfaat (tahun)"])
                reporting_year = int(asset["Tahun Pelaporan"])

                asset_caps = capitalizations_df[capitalizations_df["Nama Aset"] == asset_name].to_dict("records")
                asset_corrs = corrections_df[corrections_df["Nama Aset"] == asset_name].to_dict("records")

                schedule = calculate_depreciation(
                    initial_cost, acquisition_year, useful_life, reporting_year, asset_caps, asset_corrs
                )

                results.append({
                    "Nama Aset": asset_name,
                    "Tahun Pelaporan": reporting_year,
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

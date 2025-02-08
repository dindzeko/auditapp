import streamlit as st
from datetime import datetime
import pandas as pd
import io

# Fungsi perhitungan penyusutan semesteran
def calculate_depreciation(initial_cost, acquisition_date, useful_life, reporting_date, capitalizations=None, corrections=None):
    if capitalizations is None:
        capitalizations = []
    if corrections is None:
        corrections = []

    # Konversi masa manfaat ke semester
    useful_life_semesters = useful_life * 2
    remaining_life = useful_life_semesters
    original_life = useful_life_semesters

    # Organize capitalizations by year and semester
    cap_dict = {}
    for cap in capitalizations:
        cap_year = cap['date'].year
        cap_semester = 1 if cap['date'].month <= 6 else 2
        key = (cap_year, cap_semester)
        cap_dict.setdefault(key, []).append(cap)

    # Organize corrections by year and semester
    correction_dict = {}
    for corr in corrections:
        corr_year = corr['date'].year
        corr_semester = 1 if corr['date'].month <= 6 else 2
        key = (corr_year, corr_semester)
        correction_dict.setdefault(key, []).append(corr)

    # Initialize variables
    book_value = initial_cost
    current_year = acquisition_date.year
    current_semester = 1 if acquisition_date.month <= 6 else 2
    reporting_year = reporting_date.year
    reporting_semester = 1 if reporting_date.month <= 6 else 2
    reporting_key = (reporting_year, reporting_semester)
    accumulated_dep = 0
    schedule = []

    # Calculate depreciation semester by semester
    while remaining_life > 0 and (current_year, current_semester) <= reporting_key:
        current_key = (current_year, current_semester)

        # Process capitalizations
        if current_key in cap_dict:
            for cap in cap_dict[current_key]:
                book_value += cap['amount']
                life_extension = cap.get('life_extension', 0) * 2  # Convert years to semesters
                remaining_life = min(remaining_life + life_extension, original_life)

        # Process corrections
        if current_key in correction_dict:
            for corr in correction_dict[current_key]:
                book_value -= corr['amount']

        # Ensure book value does not become negative
        book_value = max(book_value, 0)

        if remaining_life <= 0 or book_value <= 0:
            break

        # Calculate depreciation for the current semester
        dep_per_semester = book_value / remaining_life
        accumulated_dep += dep_per_semester

        # Add to schedule
        schedule.append({
            'year': current_year,
            'semester': current_semester,
            'depreciation': round(dep_per_semester, 2),
            'accumulated': round(accumulated_dep, 2),
            'book_value': round(book_value - dep_per_semester, 2),
            'sisa_mm': remaining_life - 1
        })

        # Update values for the next semester
        book_value -= dep_per_semester
        remaining_life -= 1

        # Move to the next semester
        if current_semester == 1:
            current_semester = 2
        else:
            current_semester = 1
            current_year += 1

    return schedule

# Fungsi utama aplikasi
def app():
    st.title("📊 SHZ_Penyusutan Semesteran")

    # Inisialisasi session state
    if 'capitalizations' not in st.session_state:
        st.session_state.capitalizations = []
    if 'corrections' not in st.session_state:
        st.session_state.corrections = []

    # Input Parameter Utama
    col1, col2 = st.columns(2)
    with col1:
        acquisition_date = st.date_input(
            "📅 Tanggal Perolehan",
            value=datetime(2023, 1, 1),
            min_value=datetime(1900, 1, 1),
            max_value=datetime(2024, 12, 31)
        )
        initial_cost = st.number_input("💰 Harga Perolehan Awal (Rp)", min_value=0.0, format="%.2f")
        if acquisition_date.year < 1900 or acquisition_date.year > 2024:
            st.error("❌ Tanggal Perolehan harus antara tahun 1900 sampai 2024")
            st.stop()

    with col2:
        useful_life = st.number_input("⏳ Masa Manfaat (tahun)", min_value=1, step=1)
        reporting_date = st.date_input(
            "📅 Tanggal Pelaporan",
            value=datetime(2024, 12, 31),
            min_value=datetime(1900, 1, 1),
            max_value=datetime(2024, 12, 31)
        )

    # Form Kapitalisasi
    with st.expander("➕ Tambah Kapitalisasi"):
        with st.form("kapitalisasi_form"):
            cap_col1, cap_col2, cap_col3 = st.columns(3)
            with cap_col1:
                cap_date = st.date_input("📅 Tanggal Kapitalisasi", key="cap_date")
            with cap_col2:
                cap_amount = st.number_input("💰 Jumlah (Rp)", key="cap_amount", min_value=0.0)
            with cap_col3:
                life_extension = st.number_input("⏳ Perpanjangan Masa Manfaat (tahun)", key="life_ext", min_value=0, step=1)

            if st.form_submit_button("Tambah Kapitalisasi"):
                if cap_date < acquisition_date or cap_date > reporting_date:
                    st.error("❌ Tanggal harus antara Tanggal Perolehan dan Pelaporan")
                else:
                    st.session_state.capitalizations.append({
                        'date': cap_date,
                        'amount': cap_amount,
                        'life_extension': life_extension
                    })
                    st.success("✅ Kapitalisasi ditambahkan")

    # Tampilkan Kapitalisasi dengan Edit dan Hapus
    if st.session_state.capitalizations:
        st.subheader("📋 Rekap Kapitalisasi")
        for i, cap in enumerate(st.session_state.capitalizations):
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            with col1:
                st.write(f"**📅 Tanggal:** {cap['date'].strftime('%d/%m/%Y')}")
            with col2:
                st.write(f"**💰 Jumlah:** Rp{cap['amount']:,.2f}")
            with col3:
                st.write(f"**⏳ Perpanjangan:** {cap['life_extension']} tahun")
            with col4:
                if st.button("📝 Edit", key=f"edit_cap_{i}"):
                    st.session_state.edit_cap_index = i
                if st.button("🗑️ Hapus", key=f"delete_cap_{i}"):
                    st.session_state.capitalizations.pop(i)
                    st.rerun()

        # Form Edit Kapitalisasi
        if 'edit_cap_index' in st.session_state:
            edit_index = st.session_state.edit_cap_index
            cap_to_edit = st.session_state.capitalizations[edit_index]
            with st.form(f"edit_kapitalisasi_form_{edit_index}"):
                cap_col1, cap_col2, cap_col3 = st.columns(3)
                with cap_col1:
                    new_cap_date = st.date_input("📅 Tanggal Baru", value=cap_to_edit['date'], key=f"new_cap_date_{edit_index}")
                with cap_col2:
                    new_cap_amount = st.number_input("💰 Jumlah Baru (Rp)", value=cap_to_edit['amount'], min_value=0.0, key=f"new_cap_amount_{edit_index}")
                with cap_col3:
                    new_life_extension = st.number_input("⏳ Perpanjangan Baru (tahun)", value=cap_to_edit['life_extension'], min_value=0, step=1, key=f"new_life_ext_{edit_index}")

                if st.form_submit_button("💾 Simpan Perubahan"):
                    if new_cap_date < acquisition_date or new_cap_date > reporting_date:
                        st.error("❌ Tanggal harus antara Tanggal Perolehan dan Pelaporan")
                    else:
                        st.session_state.capitalizations[edit_index] = {
                            'date': new_cap_date,
                            'amount': new_cap_amount,
                            'life_extension': new_life_extension
                        }
                        del st.session_state.edit_cap_index
                        st.rerun()

    # Form Koreksi
    with st.expander("✏️ Tambah Koreksi"):
        with st.form("koreksi_form"):
            corr_col1, corr_col2 = st.columns(2)
            with corr_col1:
                corr_date = st.date_input("📅 Tanggal Koreksi", key="corr_date")
            with corr_col2:
                corr_amount = st.number_input("💰 Jumlah Koreksi (Rp)", key="corr_amount", min_value=0.0)

            if st.form_submit_button("Tambah Koreksi"):
                if corr_date < acquisition_date or corr_date > reporting_date:
                    st.error("❌ Tanggal harus antara Tanggal Perolehan dan Pelaporan")
                else:
                    st.session_state.corrections.append({
                        'date': corr_date,
                        'amount': corr_amount
                    })
                    st.success("✅ Koreksi ditambahkan")

    # Tampilkan Koreksi dengan Edit dan Hapus
    if st.session_state.corrections:
        st.subheader("📋 Rekap Koreksi")
        for i, corr in enumerate(st.session_state.corrections):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**📅 Tanggal:** {corr['date'].strftime('%d/%m/%Y')}")
            with col2:
                st.write(f"**💰 Jumlah:** Rp{corr['amount']:,.2f}")
            with col3:
                if st.button("📝 Edit", key=f"edit_corr_{i}"):
                    st.session_state.edit_corr_index = i
                if st.button("🗑️ Hapus", key=f"delete_corr_{i}"):
                    st.session_state.corrections.pop(i)
                    st.rerun()

        # Form Edit Koreksi
        if 'edit_corr_index' in st.session_state:
            edit_index = st.session_state.edit_corr_index
            corr_to_edit = st.session_state.corrections[edit_index]
            with st.form(f"edit_koreksi_form_{edit_index}"):
                corr_col1, corr_col2 = st.columns(2)
                with corr_col1:
                    new_corr_date = st.date_input("📅 Tanggal Baru", value=corr_to_edit['date'], key=f"new_corr_date_{edit_index}")
                with corr_col2:
                    new_corr_amount = st.number_input("💰 Jumlah Baru (Rp)", value=corr_to_edit['amount'], min_value=0.0, key=f"new_corr_amount_{edit_index}")

                if st.form_submit_button("💾 Simpan Perubahan"):
                    if new_corr_date < acquisition_date or new_corr_date > reporting_date:
                        st.error("❌ Tanggal harus antara Tanggal Perolehan dan Pelaporan")
                    else:
                        st.session_state.corrections[edit_index] = {
                            'date': new_corr_date,
                            'amount': new_corr_amount
                        }
                        del st.session_state.edit_corr_index
                        st.rerun()

    # Tombol Aksi
    action_col1, action_col2, action_col3 = st.columns([1, 1, 2])
    with action_col1:
        if st.button("🔄 Reset Semua"):
            st.session_state.capitalizations = []
            st.session_state.corrections = []
            st.rerun()

    with action_col2:
        if st.button("💾 Export Excel"):
            if 'schedule' in st.session_state:
                df = pd.DataFrame(st.session_state.schedule)
                df['Semester'] = df['semester'].apply(lambda x: f"Semester {x}")
                df = df.rename(columns={
                    'year': 'Tahun',
                    'semester': 'Semester',
                    'depreciation': 'Penyusutan',
                    'accumulated': 'Akumulasi',
                    'book_value': 'Nilai Buku',
                    'sisa_mm': 'Sisa MM'
                })

                # Konversi format mata uang
                currency_cols = ['Penyusutan', 'Akumulasi', 'Nilai Buku']
                for col in currency_cols:
                    df[col] = df[col].apply(lambda x: f"Rp{x:,.2f}")

                # Export ke Excel
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Jadwal Penyusutan')

                    # Format kolom mata uang di Excel
                    workbook = writer.book
                    worksheet = writer.sheets['Jadwal Penyusutan']
                    money_format = workbook.add_format({'num_format': '#,##0.00'})
                    for i, col in enumerate(df.columns):
                        if col in currency_cols:
                            worksheet.set_column(i, i, None, money_format)

                excel_buffer.seek(0)
                st.download_button(
                    label="📥 Download Excel",
                    data=excel_buffer,
                    file_name="jadwal_penyusutan.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    # Hitung Penyusutan
    if st.button("🧮 Hitung Penyusutan"):
        try:
            schedule = calculate_depreciation(
                initial_cost=initial_cost,
                acquisition_date=acquisition_date,
                useful_life=useful_life,
                reporting_date=reporting_date,
                capitalizations=st.session_state.capitalizations,
                corrections=st.session_state.corrections
            )
            st.session_state.schedule = schedule

            # Format hasil untuk tampilan
            df = pd.DataFrame(schedule)
            df['Semester'] = df['semester'].apply(lambda x: f"Semester {x}")
            df['Penyusutan'] = df['depreciation'].apply(lambda x: f"Rp{x:,.2f}")
            df['Akumulasi'] = df['accumulated'].apply(lambda x: f"Rp{x:,.2f}")
            df['Nilai Buku'] = df['book_value'].apply(lambda x: f"Rp{x:,.2f}")

            st.subheader("📊 Jadwal Penyusutan")
            st.dataframe(df[['year', 'Semester', 'Penyusutan', 'Akumulasi', 'Nilai Buku', 'sisa_mm']].rename(
                columns={'year': 'Tahun', 'sisa_mm': 'Sisa MM'}
            ), use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"❌ Terjadi kesalahan: {str(e)}")

import streamlit as st
from datetime import datetime
import pandas as pd
import io

# Fungsi perhitungan depresiasi tahunan
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
                book_value += cap['amount']
                life_extension = cap.get('life_extension', 0)
                remaining_life = min(remaining_life + life_extension, original_life)

        # Process corrections
        if current_year in corr_dict:
            for corr in corr_dict[current_year]:
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

# Inisialisasi session state
if "capitalizations" not in st.session_state:
    st.session_state.capitalizations = []
if "corrections" not in st.session_state:
    st.session_state.corrections = []

# Judul aplikasi
st.title("📉 Depresiasi Garis Lurus Tahunan")

# Informasi Penggunaan
with st.expander("📝 Panduan Penggunaan ▼", expanded=False):
    st.markdown("""
    ### Cara Menggunakan Aplikasi Ini:
    1. **Masukkan Parameter Input**:
       - **Harga Perolehan Awal**: Masukkan harga awal aset dalam Rupiah.
       - **Tahun Perolehan**: Tahun ketika aset diperoleh.
       - **Masa Manfaat**: Jumlah tahun aset akan disusutkan.
       - **Tahun Pelaporan**: Tahun hingga penyusutan dihitung.
    
    2. **Tambahkan Kapitalisasi**:
       - Masukkan tahun, jumlah kapitalisasi, dan tambahan masa manfaat (jika ada).
       - Klik tombol **Tambah Kapitalisasi** untuk menyimpan data.
    
    3. **Tambahkan Koreksi**:
       - Masukkan tahun dan jumlah koreksi.
       - Klik tombol **Tambah Koreksi** untuk menyimpan data.
    
    4. **Hitung Penyusutan**:
       - Setelah semua data dimasukkan, klik tombol **Hitung Penyusutan**.
       - Hasil perhitungan akan ditampilkan dalam tabel.
    
    5. **Download Hasil**:
       - Anda dapat mendownload hasil perhitungan dalam format Excel dengan mengklik tombol **Download Excel**.
    """)

# Input Parameter
st.header("📥 Parameter Input")
col1, col2 = st.columns(2)
with col1:
    initial_cost = st.number_input("💰 Harga Perolehan Awal (Rp)", min_value=0.0, step=1000000.0, format="%.2f")
    acquisition_year = st.number_input("📅 Tahun Perolehan", min_value=1900, max_value=2100, step=1)
with col2:
    useful_life = st.number_input("⏳ Masa Manfaat (tahun)", min_value=1, step=1)
    reporting_year = st.number_input("📅 Tahun Pelaporan", min_value=1900, max_value=2100, step=1, value=datetime.now().year)

# Form Kapitalisasi
with st.expander("➕ Tambah Kapitalisasi"):
    with st.form("kapitalisasi_form"):
        cap_col1, cap_col2, cap_col3 = st.columns(3)
        with cap_col1:
            cap_year = st.number_input("📅 Tahun Kapitalisasi", key="cap_year", min_value=1900, max_value=2100, step=1)
        with cap_col2:
            cap_amount = st.number_input("💰 Jumlah (Rp)", key="cap_amount", min_value=0.0, step=1000000.0)
        with cap_col3:
            cap_life = st.number_input("⏳ Tambahan Masa Manfaat (tahun)", key="cap_life", min_value=0, step=1)

        if st.form_submit_button("Tambah Kapitalisasi"):
            if cap_year < acquisition_year or cap_year > reporting_year:
                st.error("❌ Tahun harus antara Tahun Perolehan dan Pelaporan")
            else:
                st.session_state.capitalizations.append({
                    'year': cap_year,
                    'amount': cap_amount,
                    'life_extension': cap_life
                })
                st.success("✅ Kapitalisasi ditambahkan")

# Tampilkan Kapitalisasi dengan Edit dan Hapus
if st.session_state.capitalizations:
    st.subheader("📋 Rekap Kapitalisasi")
    for i, cap in enumerate(st.session_state.capitalizations):
        col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
        with col1:
            st.write(f"**📅 Tahun:** {cap['year']}")
        with col2:
            st.write(f"**💰 Jumlah:** Rp{cap['amount']:,.2f}")
        with col3:
            st.write(f"**⏳ Tambahan MM:** {cap['life_extension']} tahun")
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
                new_cap_year = st.number_input("📅 Tahun Baru", value=cap_to_edit['year'], min_value=1900, max_value=2100, key=f"new_cap_year_{edit_index}")
            with cap_col2:
                new_cap_amount = st.number_input("💰 Jumlah Baru (Rp)", value=cap_to_edit['amount'], min_value=0.0, step=1000000.0, key=f"new_cap_amount_{edit_index}")
            with cap_col3:
                new_cap_life = st.number_input("⏳ Tambahan MM Baru (tahun)", value=cap_to_edit['life_extension'], min_value=0, step=1, key=f"new_cap_life_{edit_index}")

            if st.form_submit_button("💾 Simpan Perubahan"):
                if new_cap_year < acquisition_year or new_cap_year > reporting_year:
                    st.error("❌ Tahun harus antara Tahun Perolehan dan Pelaporan")
                else:
                    st.session_state.capitalizations[edit_index] = {
                        'year': new_cap_year,
                        'amount': new_cap_amount,
                        'life_extension': new_cap_life
                    }
                    del st.session_state.edit_cap_index
                    st.rerun()

# Form Koreksi
with st.expander("✏️ Tambah Koreksi"):
    with st.form("koreksi_form"):
        corr_col1, corr_col2 = st.columns(2)
        with corr_col1:
            corr_year = st.number_input("📅 Tahun Koreksi", key="corr_year", min_value=1900, max_value=2100, step=1)
        with corr_col2:
            corr_amount = st.number_input("💰 Jumlah Koreksi (Rp)", key="corr_amount", min_value=0.0, step=1000000.0)

        if st.form_submit_button("Tambah Koreksi"):
            if corr_year < acquisition_year or corr_year > reporting_year:
                st.error("❌ Tahun harus antara Tahun Perolehan dan Pelaporan")
            else:
                st.session_state.corrections.append({
                    'year': corr_year,
                    'amount': corr_amount
                })
                st.success("✅ Koreksi ditambahkan")

# Tampilkan Koreksi dengan Edit dan Hapus
if st.session_state.corrections:
    st.subheader("📋 Rekap Koreksi")
    for i, corr in enumerate(st.session_state.corrections):
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            st.write(f"**📅 Tahun:** {corr['year']}")
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
                new_corr_year = st.number_input("📅 Tahun Baru", value=corr_to_edit['year'], min_value=1900, max_value=2100, key=f"new_corr_year_{edit_index}")
            with corr_col2:
                new_corr_amount = st.number_input("💰 Jumlah Baru (Rp)", value=corr_to_edit['amount'], min_value=0.0, step=1000000.0, key=f"new_corr_amount_{edit_index}")

            if st.form_submit_button("💾 Simpan Perubahan"):
                if new_corr_year < acquisition_year or new_corr_year > reporting_year:
                    st.error("❌ Tahun harus antara Tahun Perolehan dan Pelaporan")
                else:
                    st.session_state.corrections[edit_index] = {
                        'year': new_corr_year,
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
            df['Penyusutan'] = df['depreciation'].apply(lambda x: f"Rp{x:,.2f}")
            df['Akumulasi'] = df['accumulated'].apply(lambda x: f"Rp{x:,.2f}")
            df['Nilai Buku'] = df['book_value'].apply(lambda x: f"Rp{x:,.2f}")

            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Jadwal Penyusutan')

                workbook = writer.book
                worksheet = writer.sheets['Jadwal Penyusutan']
                money_format = workbook.add_format({'num_format': '#,##0.00'})
                for i, col in enumerate(df.columns):
                    if col in ['Penyusutan', 'Akumulasi', 'Nilai Buku']:
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
            acquisition_year=acquisition_year,
            useful_life=useful_life,
            reporting_year=reporting_year,
            capitalizations=st.session_state.capitalizations,
            corrections=st.session_state.corrections
        )
        st.session_state.schedule = schedule

        # Format hasil untuk tampilan
        df = pd.DataFrame(schedule)
        df['Penyusutan'] = df['depreciation'].apply(lambda x: f"Rp{x:,.2f}")
        df['Akumulasi'] = df['accumulated'].apply(lambda x: f"Rp{x:,.2f}")
        df['Nilai Buku'] = df['book_value'].apply(lambda x: f"Rp{x:,.2f}")

        st.subheader("📊 Jadwal Penyusutan")
        st.dataframe(df[['year', 'Penyusutan', 'Akumulasi', 'Nilai Buku', 'sisa_mm']].rename(
            columns={'year': 'Tahun', 'sisa_mm': 'Sisa MM'}
        ), use_container_width=True, hide_index=True)

    except Exception as e:
        st.error(f"❌ Terjadi kesalahan: {str(e)}")

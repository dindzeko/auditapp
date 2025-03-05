import streamlit as st
import pandas as pd
from datetime import datetime

# Fungsi-fungsi helper
def delete_capitalization(index):
    st.session_state.capitalizations.pop(index)

def edit_capitalization(index):
    st.session_state.editing_cap_index = index

def delete_correction(index):
    st.session_state.corrections.pop(index)

def edit_correction(index):
    st.session_state.editing_corr_index = index

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

def convert_df_to_excel(df):
    import io
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
        writer.close()
    return buffer.getvalue()

def format_number_indonesia(number):
    if isinstance(number, (int, float)):
        return f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return number

# Fungsi utama aplikasi
def app():
    st.title("📉 Depresiasi GL Tahunan")

    # Informasi Penggunaan dengan Toggle (Expander)
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
        
        3. **Tambahkan Koreksi Kurang**:
           - Masukkan tahun dan jumlah koreksi kurang aset tetap.
           - Klik tombol **Tambah Koreksi** untuk menyimpan data.
        
        4. **Hitung Penyusutan**:
           - Setelah semua data dimasukkan, klik tombol **Hitung Penyusutan**.
           - Hasil perhitungan akan ditampilkan dalam tabel.
        
        5. **Download Hasil**:
           - Anda dapat mendownload hasil perhitungan dalam format Excel dengan mengklik tombol **Download Excel**.
        """)

    # Main Content
    st.header("📥 Parameter Input")
    with st.expander("📅 Parameter Input", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            initial_cost = st.number_input(
                "Harga Perolehan Awal (Rp)",
                min_value=0.0,
                step=1000000.0,
                format="%.2f"
            )
            acquisition_year = st.number_input(
                "Tahun Perolehan",
                min_value=1900,
                max_value=datetime.now().year,
                step=1
            )
        with col2:
            useful_life = st.number_input(
                "Masa Manfaat (tahun)",
                min_value=1,
                max_value=100, 
                step=1
            )
            reporting_year = st.number_input(
                "Tahun Pelaporan",
                min_value=2006,
                max_value=2100,
                step=1,
                value=datetime.now().year-1
            )

    # Tombol Reset
    action_col1, action_col2 = st.columns([1, 3])
    with action_col1:
        if st.button("🔄 Reset Semua"):
            st.session_state.capitalizations = []
            st.session_state.corrections = []
            st.rerun()

    # Capitalization Management
    st.header("➕ Input Kapitalisasi")
    with st.expander("➕ Tambah Kapitalisasi", expanded=True):
        if "capitalizations" not in st.session_state:
            st.session_state.capitalizations = []
        col_cap1, col_cap2, col_cap3 = st.columns(3)
        with col_cap1:
            cap_year = st.number_input("Tahun", key="cap_year", min_value=1900, max_value=2100, step=1)
        with col_cap2:
            cap_amount = st.number_input("Jumlah", key="cap_amount", min_value=0.0, step=1000000.0)
        with col_cap3:
            cap_life = st.number_input("Tambahan Usia", key="cap_life", min_value=0, step=1)
        if st.button("Tambah Kapitalisasi", key="add_cap"):
            if cap_year < acquisition_year:
                st.error("Tahun Kapitalisasi tidak boleh lebih awal dari Tahun Perolehan")
            else:
                st.session_state.capitalizations.append({
                    'year': cap_year,
                    'amount': cap_amount,
                    'life_extension': cap_life
                })

    # Correction Management
    st.header("✏️ Input Koreksi")
    with st.expander("✏️ Tambah Koreksi", expanded=True):
        if "corrections" not in st.session_state:
            st.session_state.corrections = []
        col_corr1, col_corr2 = st.columns(2)
        with col_corr1:
            corr_year = st.number_input("Tahun", key="corr_year", min_value=1900, max_value=2100, step=1)
        with col_corr2:
            corr_amount = st.number_input("Jumlah", key="corr_amount", min_value=0.0, step=1000000.0)
        if st.button("Tambah Koreksi", key="add_corr"):
            if corr_year < acquisition_year:
                st.error("Tahun Koreksi tidak boleh lebih awal dari Tahun Perolehan")
            else:
                st.session_state.corrections.append({
                    'year': corr_year,
                    'amount': corr_amount
                })

    # Display Data
    st.header("📊 Data Input")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Kapitalisasi")
        if st.session_state.capitalizations:
            cap_df = pd.DataFrame(st.session_state.capitalizations)
            cap_df["amount"] = cap_df["amount"].apply(format_number_indonesia)
            st.dataframe(cap_df, hide_index=True)
            for i, _ in enumerate(st.session_state.capitalizations):
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.button(
                        f"Hapus Kapitalisasi {i+1}",
                        key=f"del_cap_{i}",
                        on_click=delete_capitalization,
                        args=(i,)
                    )
                with col_btn2:
                    st.button(
                        f"Edit Kapitalisasi {i+1}",
                        key=f"edit_cap_{i}",
                        on_click=edit_capitalization,
                        args=(i,)
                    )
            if 'editing_cap_index' in st.session_state:
                i = st.session_state.editing_cap_index
                cap = st.session_state.capitalizations[i]
                new_year = st.number_input("Tahun", value=cap['year'], min_value=1900, max_value=2100, key=f"edit_cap_year_{i}")
                new_amount = st.number_input("Jumlah", value=cap['amount'], min_value=0.0, step=1000000.0, key=f"edit_cap_amount_{i}")
                new_life = st.number_input("Tambahan Usia", value=cap['life_extension'], min_value=0, step=1, key=f"edit_cap_life_{i}")
                if st.button("Simpan Perubahan", key=f"save_cap_{i}"):
                    if new_year < acquisition_year:
                        st.error("Tahun Kapitalisasi tidak boleh lebih awal dari Tahun Perolehan")
                    else:
                        st.session_state.capitalizations[i] = {
                            'year': new_year,
                            'amount': new_amount,
                            'life_extension': new_life
                        }
                        del st.session_state.editing_cap_index
                        st.rerun()
                if st.button("Batal", key=f"cancel_cap_{i}"):
                    del st.session_state.editing_cap_index
                    st.rerun()
        else:
            st.info("Tidak ada data kapitalisasi")
    with col2:
        st.subheader("Koreksi")
        if st.session_state.corrections:
            corr_df = pd.DataFrame(st.session_state.corrections)
            corr_df["amount"] = corr_df["amount"].apply(format_number_indonesia)
            st.dataframe(corr_df, hide_index=True)
            for i, _ in enumerate(st.session_state.corrections):
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    st.button(
                        f"Hapus Koreksi {i+1}",
                        key=f"del_corr_{i}",
                        on_click=delete_correction,
                        args=(i,)
                    )
                with col_btn2:
                    st.button(
                        f"Edit Koreksi {i+1}",
                        key=f"edit_corr_{i}",
                        on_click=edit_correction,
                        args=(i,)
                    )
            if 'editing_corr_index' in st.session_state:
                i = st.session_state.editing_corr_index
                corr = st.session_state.corrections[i]
                new_year = st.number_input("Tahun", value=corr['year'], min_value=1900, max_value=2100, key=f"edit_corr_year_{i}")
                new_amount = st.number_input("Jumlah", value=corr['amount'], min_value=0.0, step=1000000.0, key=f"edit_corr_amount_{i}")
                if st.button("Simpan Perubahan", key=f"save_corr_{i}"):
                    if new_year < acquisition_year:
                        st.error("Tahun Koreksi tidak boleh lebih awal dari Tahun Perolehan")
                    else:
                        st.session_state.corrections[i] = {
                            'year': new_year,
                            'amount': new_amount
                        }
                        del st.session_state.editing_corr_index
                        st.rerun()
                if st.button("Batal", key=f"cancel_corr_{i}"):
                    del st.session_state.editing_corr_index
                    st.rerun()
        else:
            st.info("Tidak ada data koreksi")

    # Calculation and Results
    if st.button("🚀 Hitung Penyusutan", use_container_width=True):
        error_messages = []
        # Basic validations
        if initial_cost <= 0:
            error_messages.append("Harga perolehan awal harus lebih besar dari 0")
        if acquisition_year > reporting_year:
            error_messages.append("Tahun perolehan tidak boleh lebih besar dari tahun pelaporan")
        if error_messages:
            for msg in error_messages:
                st.error(msg)
        else:
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

   # Export Excel
if 'schedule' in st.session_state:
    # Buat DataFrame dari jadwal penyusutan
    df = pd.DataFrame(st.session_state.schedule)

    # Format kolom dalam bahasa Indonesia
    df_export = pd.DataFrame({
        'Tahun': df['year'],
        'Penyusutan': df['depreciation'].apply(lambda x: f"Rp{x:,.2f}"),
        'Akumulasi': df['accumulated'].apply(lambda x: f"Rp{x:,.2f}"),
        'Nilai Buku': df['book_value'].apply(lambda x: f"Rp{x:,.2f}"),
        'Sisa MM': df['sisa_mm']
    })

    # Konversi ke Excel
    excel_buffer = convert_df_to_excel(df_export)

    # Tombol unduh
    st.download_button(
        label="📥 Download Excel",
        data=excel_buffer,
        file_name="jadwal_penyusutan.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Jalankan aplikasi
if __name__ == "__main__":
    app()

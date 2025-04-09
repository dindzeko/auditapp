import streamlit as st
import pandas as pd
from io import BytesIO

def app():
    # Tambahkan CSS inline untuk mengurangi jarak antar pilihan multiselect
    st.markdown(
        """
        <style>
            .stMultiSelect div[role="listbox"] {
                column-count: 3; /* Ubah menjadi kolom 3 untuk mengurangi jarak */
                column-gap: 5px; /* Atur jarak antar kolom */
            }
            .stMultiSelect div[role="listbox"] > div {
                margin-bottom: 1px; /* Atur jarak antar elemen */
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.title("Buku Besar Transaksi")

    # ================== DATA LOADING ==================
    if "bukubesar" not in st.session_state:
        try:
            st.session_state["bukubesar"] = pd.read_excel(
                "data/bukubesar.xlsb",
                engine="pyxlsb"
            )
        except Exception as e:
            st.error(f"Gagal memuat data bukubesar: {str(e)}")
            return

    if "coa" not in st.session_state:
        try:
            st.session_state["coa"] = pd.read_excel("data/coa.xlsx")
            # Konversi semua kode akun ke string
            for col in st.session_state["coa"].columns:
                if 'Kode Akun' in col:
                    st.session_state["coa"][col] = st.session_state["coa"][col].astype(str).str.strip()
        except Exception as e:
            st.error(f"Gagal memuat data coa: {str(e)}")
            return

    bukubesar = st.session_state["bukubesar"]
    coa = st.session_state["coa"]

    # ================== PREPROCESSING ==================
    try:
        if "tgl_transaksi" in bukubesar.columns:
            # Parsing tanggal dengan format dd/mm/yyyy atau serial Excel
            if bukubesar["tgl_transaksi"].dtype in ["float64", "int64"]:
                bukubesar["tgl_transaksi"] = pd.to_datetime(
                    bukubesar["tgl_transaksi"], 
                    unit="D", 
                    origin="1899-12-30"
                )
            else:
                bukubesar["tgl_transaksi"] = pd.to_datetime(
                    bukubesar["tgl_transaksi"],
                    format="%d/%m/%Y",
                    errors="coerce"
                )
            bukubesar = bukubesar.dropna(subset=["tgl_transaksi"])
        else:
            st.error("Kolom 'tgl_transaksi' tidak ditemukan")
            return
    except Exception as e:
        st.error(f"Gagal memproses tanggal: {str(e)}")
        return

    # ================== LEVEL 1 CATEGORIES ==================
    level1_mapping = {
        '1': 'ASET',
        '2': 'KEWAJIBAN',
        '3': 'EKUITAS', 
        '4': 'PENDAPATAN DAERAH',
        '5': 'BELANJA DAERAH',
        '6': 'PEMBIAYAAN DAERAH',
        '7': 'PENDAPATAN DAERAH-LO',
        '8': 'BEBAN DAERAH'
    }

    # ================== WIDGET FILTER ==================
    st.subheader("Filter Data")
    st.markdown("---")

    # 1. Filter Jenis Transaksi
    st.write("### Pilih Jenis Transaksi:")
    jenis_transaksi_options = [
        "Jurnal Balik","Jurnal Eliminasi", "Jurnal Koreksi", "Jurnal Non RKUD", "Jurnal Pembiayaan", 
        "Jurnal Penerimaan", "Jurnal Pengeluaran", "Jurnal Penutup", 
        "Jurnal Penyesuaian", "Jurnal Umum", "Saldo Awal"
    ]
    selected_jenis_transaksi = st.multiselect(
        "Jenis Transaksi", options=jenis_transaksi_options, default=jenis_transaksi_options
    )
    st.markdown("---")

    # 2. Filter Unit (SKPD atau All)
    st.write("### Pilih Unit:")
    selected_unit = st.radio("Unit", ["All", "SKPD"], index=0)
    selected_skpd = None
    if selected_unit == "SKPD":
        skpd_options = bukubesar["nm_unit"].unique()
        selected_skpd = st.selectbox("Pilih SKPD", options=skpd_options)
    st.markdown("---")

    # 3. Filter Level Akun
    st.write("### Pilih Level Akun:")
    selected_level = st.selectbox("Level", options=[f"Level {i}" for i in range(1, 7)])
    target_level = int(selected_level.split()[-1])
    st.markdown("---")

    # 4. Filter Kategori Akun
    st.write("### Pilih Akun Induk:")
    if target_level == 1:
        # Khusus Level 1 menggunakan mapping tetap
        kategori_options = list(level1_mapping.values())
        selected_kategori = st.selectbox("Kategori", options=kategori_options)
        selected_kode = [k for k, v in level1_mapping.items() if v == selected_kategori][0]
    else:
        # Untuk level 2-6 ambil dari struktur COA
        parent_level = target_level - 1
        parent_col = f"Kode Akun {parent_level}"
        name_col = f"Nama Akun {parent_level}"
        
        if parent_col not in coa.columns or name_col not in coa.columns:
            st.error(f"Struktur COA tidak valid untuk level {target_level}")
            return
        
        kategori_options = coa[[parent_col, name_col]].drop_duplicates().dropna()
        selected_parent = st.selectbox(
            "Kategori Induk",
            options=kategori_options[name_col]
        )
        selected_kode = kategori_options[
            kategori_options[name_col] == selected_parent
        ][parent_col].iloc[0]

    st.markdown("---")

    # 5. Filter Akun Spesifik
    st.write("### Pilih Buku Besar Akun:")
    target_col = f"Kode Akun {target_level}"
    filtered_coa = coa[coa[target_col].fillna("").astype(str).str.startswith(selected_kode)]
    akun_options = filtered_coa[f"Nama Akun {target_level}"].unique()
    
    if len(akun_options) > 0:
        selected_akun = st.selectbox("Nama Akun", akun_options)
        kode_akun = filtered_coa[
            filtered_coa[f"Nama Akun {target_level}"] == selected_akun
        ][target_col].iloc[0]
    else:
        st.warning("Tidak ada akun tersedia")
        return
    
    st.markdown("---")

    # 6. Filter Tipe Transaksi (Debet/Kredit/All)
    st.write("### Pilih Tipe Transaksi:")
    transaction_type = st.radio(
        "Tipe Transaksi", options=["Debet", "Kredit", "All"], horizontal=True
    )
    st.markdown("---")

    # ================== PROCESS DATA ==================
    if st.button("Proses Data"):
        try:
            filtered_data = bukubesar.copy()
            
            # Bersihkan kolom debet dan kredit dari nilai non-numerik
            filtered_data["debet"] = pd.to_numeric(filtered_data["debet"], errors="coerce")
            filtered_data["kredit"] = pd.to_numeric(filtered_data["kredit"], errors="coerce")
            
            # Ganti nilai NaN dengan 0
            filtered_data["debet"] = filtered_data["debet"].fillna(0)
            filtered_data["kredit"] = filtered_data["kredit"].fillna(0)
            
            # Filter akun berdasarkan kategori
            filtered_data = filtered_data[
                filtered_data["kd_lv_6"].astype(str).str.startswith(kode_akun)
            ]
            
            # Filter jenis transaksi
            if selected_jenis_transaksi:
                filtered_data = filtered_data[filtered_data["jns_transaksi"].isin(selected_jenis_transaksi)]
            
            # Filter tipe transaksi
            if transaction_type == "Debet":
                filtered_data = filtered_data[filtered_data["debet"] > 0]
            elif transaction_type == "Kredit":
                filtered_data = filtered_data[filtered_data["kredit"] > 0]
            
            # Filter unit
            if selected_unit == "SKPD" and selected_skpd:
                filtered_data = filtered_data[filtered_data["nm_unit"] == selected_skpd]
            
            # Gabungkan dengan COA untuk tampilkan nama akun
            merged_data = pd.merge(
                filtered_data,
                coa[["Kode Akun 6", "Nama Akun 6"]],
                left_on="kd_lv_6",
                right_on="Kode Akun 6",
                how="left"
            )
            
            # Hitung saldo akun
            saldo_akun = merged_data["debet"].sum() - merged_data["kredit"].sum()
            
            # Tampilkan saldo akun di atas tabel hasil filter
            st.subheader("Saldo Akun")
            st.write(f"Saldo ({selected_akun}): Rp {saldo_akun:,.0f}")
            
            # Generate nama file dinamis
            unit_name = selected_skpd if selected_unit == "SKPD" else "All"
            file_name = f"{unit_name}_{selected_level}_{selected_akun}.xlsx"
            
            # Tampilkan hasil filter
            st.subheader("Hasil Filter")
            top_n = st.number_input("Tampilkan Berapa Baris Teratas?", min_value=1, value=20)
            display_data = merged_data.head(top_n)[[
                "no_bukti", "tgl_transaksi", "jns_transaksi", "nm_unit",
                "kd_lv_6", "Nama Akun 6", "debet", "kredit", "uraian"
            ]]
            st.dataframe(display_data)
            
            # Download hasil
            output = BytesIO()
            with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                merged_data.to_excel(writer, index=False)
            output.seek(0)
            st.download_button(
                "Unduh Excel",
                data=output,
                file_name=file_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
        except Exception as e:
            st.error(f"Terjadi kesalahan: {str(e)}")

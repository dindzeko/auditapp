import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil import parser
from io import BytesIO  # Untuk membuat file Excel dalam memori

# Fungsi utama untuk menghitung FIFO secara Batch dilengkapi dengan kertas kerja
def calculate_batch_with_worksheet(inventory, transactions):
    """
    Menghitung persediaan akhir menggunakan metode FIFO (Batch) dan mencatat kertas kerja.
    """
    inventory = inventory.copy()
    transactions = sorted(transactions, key=lambda x: x["tanggal"])  # Urutkan berdasarkan tanggal
    
    # Kertas kerja
    worksheet = []
    
    # Saldo Awal
    worksheet.append({
        "uraian": "Saldo Awal",
        "tanggal": None,
        "tambah_kurang": "",
        "persediaan_akhir": [{"unit": item["unit"], "nilai": item["nilai"]} for item in inventory]
    })
    
    for transaksi in transactions:
        if transaksi["jenis"] == "Tambah":
            inventory.append({"unit": transaksi["unit"], "nilai": transaksi["nilai"]})
            worksheet.append({
                "uraian": f"Tambah {transaksi['unit']} unit @ {transaksi['nilai']:.2f}",
                "tanggal": transaksi["tanggal"],
                "tambah_kurang": f"+{transaksi['unit']} unit @ {transaksi['nilai']:.2f}",
                "persediaan_akhir": [{"unit": item["unit"], "nilai": item["nilai"]} for item in inventory]
            })
        elif transaksi["jenis"] == "Kurang":
            unit_to_remove = transaksi["unit"]
            while unit_to_remove > 0 and inventory:
                oldest = inventory[0]
                if oldest["unit"] <= unit_to_remove:
                    unit_to_remove -= oldest["unit"]
                    inventory.pop(0)
                else:
                    oldest["unit"] -= unit_to_remove
                    unit_to_remove = 0
            worksheet.append({
                "uraian": f"Kurang {transaksi['unit']} unit",
                "tanggal": transaksi["tanggal"],
                "tambah_kurang": f"-{transaksi['unit']} unit",
                "persediaan_akhir": [{"unit": item["unit"], "nilai": item["nilai"]} for item in inventory]
            })
    
    # Hitung Saldo Akhir
    total_unit = sum(item["unit"] for item in inventory)
    total_nilai = sum(item["unit"] * item["nilai"] for item in inventory)
    
    # Tambahkan baris Saldo Akhir ke kertas kerja
    worksheet.append({
        "uraian": "Saldo Akhir",
        "tanggal": None,
        "tambah_kurang": "",
        "persediaan_akhir": [{"unit": item["unit"], "nilai": item["nilai"]} for item in inventory],
        "total_nilai": total_nilai
    })
    
    return inventory, total_unit, total_nilai, worksheet


# Halaman Streamlit
def app():
    st.title("FIFO Inventory Calculator (Batch)")
    
    # Inisialisasi session state
    if "inventory" not in st.session_state:
        st.session_state.inventory = []
    if "transactions" not in st.session_state:
        st.session_state.transactions = []
    if "worksheet" not in st.session_state:
        st.session_state.worksheet = []  # Untuk menyimpan kertas kerja
    
    # Input Saldo Awal
    st.subheader("Saldo Awal")
    saldo_unit = st.number_input("Jumlah Unit (Saldo Awal)", min_value=0, step=1)
    saldo_nilai = st.number_input("Nilai Per Unit (Saldo Awal)", min_value=0.0, step=0.01)
    
    if st.button("Set Saldo Awal"):
        if saldo_unit > 0 and saldo_nilai > 0:
            st.session_state.inventory.append({"unit": saldo_unit, "nilai": saldo_nilai})
            st.success("Saldo awal berhasil diset!")
        else:
            st.error("Masukkan jumlah unit dan nilai per unit yang valid!")
    
    # Upload File Excel untuk Transaksi
    st.subheader("Upload Transaksi dari Excel")
    uploaded_file = st.file_uploader("Upload file Excel (.xlsx)", type=["xlsx"])
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            required_columns = {"Tanggal", "Jenis", "Unit", "Nilai"}
            if not required_columns.issubset(df.columns):
                st.error("File Excel harus memiliki kolom berikut: Tanggal, Jenis, Unit, Nilai")
                return
            
            transactions = []
            for _, row in df.iterrows():
                try:
                    tanggal = parser.parse(str(row["Tanggal"])).date()
                except ValueError:
                    st.error(f"Tanggal tidak valid: {row['Tanggal']}")
                    return
                
                jenis = str(row["Jenis"]).strip().capitalize()
                if jenis not in ["Tambah", "Kurang"]:
                    st.error(f"Jenis transaksi tidak valid: {row['Jenis']}")
                    return
                
                try:
                    unit = int(row["Unit"])
                    if unit <= 0:
                        raise ValueError
                except ValueError:
                    st.error(f"Jumlah unit tidak valid: {row['Unit']}")
                    return
                
                nilai = float(row["Nilai"]) if jenis == "Tambah" else None
                if jenis == "Tambah" and nilai <= 0:
                    st.error(f"Nilai per unit tidak valid: {row['Nilai']}")
                    return
                
                transactions.append({
                    "tanggal": tanggal,
                    "unit": unit,
                    "nilai": nilai,
                    "jenis": jenis
                })
            
            st.session_state.transactions = transactions
            st.success(f"{len(transactions)} transaksi berhasil diupload!")
        except Exception as e:
            st.error(f"Terjadi kesalahan saat membaca file Excel: {e}")
    
    # Hitung Persediaan Akhir
    if st.button("Hitung Persediaan Akhir"):
        if st.session_state.inventory:
            inventory, total_unit, total_nilai, worksheet = calculate_batch_with_worksheet(
                st.session_state.inventory, st.session_state.transactions
            )
            st.session_state.worksheet = worksheet  # Simpan kertas kerja ke session state
            
            st.subheader("Hasil Perhitungan FIFO")
            st.write(f"Total Unit: {total_unit}")
            st.write(f"Total Nilai: {total_nilai:.2f}")
            
            # Format kertas kerja menjadi tabel
            table_data = []
            for step in worksheet:
                if step["uraian"] == "Saldo Akhir":
                    # Format khusus untuk Saldo Akhir
                    persediaan_str = f"{step['total_nilai']:.2f}"
                else:
                    # Format umum untuk baris lainnya
                    persediaan_str = ", ".join(
                        [f"{item['unit']} unit @ {item['nilai']:.2f} ({item['unit'] * item['nilai']:.2f})" 
                         for item in step["persediaan_akhir"]]
                    )
                
                table_data.append({
                    "Uraian": step["uraian"],
                    "Tanggal Transaksi": step["tanggal"],
                    "Tambah/Kurang": step["tambah_kurang"],
                    "Persediaan Akhir": persediaan_str
                })
            
            # Tampilkan tabel
            st.subheader("Kertas Kerja Perhitungan FIFO")
            st.table(table_data)
        else:
            st.error("Saldo awal belum diset!")
    
    # Export ke Excel
    if st.session_state.worksheet:
        st.subheader("Export Kertas Kerja ke Excel")
        export_data = []
        for step in st.session_state.worksheet:
            if step["uraian"] == "Saldo Akhir":
                # Format khusus untuk Saldo Akhir
                persediaan_str = f"{step['total_nilai']:.2f}"
            else:
                # Format umum untuk baris lainnya
                persediaan_str = ", ".join(
                    [f"{item['unit']} unit @ {item['nilai']:.2f} ({item['unit'] * item['nilai']:.2f})" 
                     for item in step["persediaan_akhir"]]
                )
            
            export_data.append({
                "Uraian": step["uraian"],
                "Tanggal Transaksi": step["tanggal"],
                "Tambah/Kurang": step["tambah_kurang"],
                "Persediaan Akhir": persediaan_str
            })
        
        # Buat DataFrame
        df_export = pd.DataFrame(export_data)
        
        # Konversi ke file Excel dalam memori
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df_export.to_excel(writer, index=False, sheet_name="Kertas_Kerja_FIFO")
        output.seek(0)  # Pindahkan pointer ke awal file
        
        # Tombol Download
        st.download_button(
            label="Download Kertas Kerja (Excel)",
            data=output,
            file_name="kertas_kerja_fifo.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    # Reset Aplikasi
    if st.button("Reset"):
        # Hapus semua data di session state
        st.session_state.inventory.clear()
        st.session_state.transactions.clear()
        st.session_state.worksheet.clear()
        st.success("Aplikasi telah direset! Semua data telah dihapus.")


# Jalankan halaman FIFO Batch jika file dijalankan langsung
if __name__ == "__main__":
    app()

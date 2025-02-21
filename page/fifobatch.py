
import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil import parser  # Untuk mendeteksi format tanggal otomatis

# Fungsi utama untuk menghitung FIFO
def calculate_fifo(inventory, transactions):
    """
    Menghitung persediaan akhir menggunakan metode FIFO.
    """
    inventory = inventory.copy()
    transactions = sorted(transactions, key=lambda x: x["tanggal"])  # Urutkan berdasarkan tanggal

    for transaksi in transactions:
        if transaksi["jenis"] == "Tambah":
            inventory.append({"unit": transaksi["unit"], "nilai": transaksi["nilai"]})
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

    total_unit = sum(item["unit"] for item in inventory)
    total_nilai = sum(item["unit"] * item["nilai"] for item in inventory)

    return inventory, total_unit, total_nilai


# Halaman Streamlit
def fifo_page():
    st.title("FIFO Inventory Calculator")

    # Inisialisasi session state
    if "inventory" not in st.session_state:
        st.session_state.inventory = []
    if "transactions" not in st.session_state:
        st.session_state.transactions = []

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
            # Baca file Excel
            df = pd.read_excel(uploaded_file)

            # Validasi kolom
            required_columns = {"Tanggal", "Jenis", "Unit", "Nilai"}
            if not required_columns.issubset(df.columns):
                st.error("File Excel harus memiliki kolom berikut: Tanggal, Jenis, Unit, Nilai")
                return

            # Konversi data ke list transaksi
            transactions = []
            for _, row in df.iterrows():
                try:
                    # Mengonversi tanggal ke format Python datetime
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

            # Simpan transaksi ke session state
            st.session_state.transactions = transactions
            st.success(f"{len(transactions)} transaksi berhasil diupload!")
        except Exception as e:
            st.error(f"Terjadi kesalahan saat membaca file Excel: {e}")

    # Daftar Transaksi
    st.subheader("Daftar Transaksi")
    if st.session_state.transactions:
        for idx, transaksi in enumerate(st.session_state.transactions, start=1):
            if transaksi["jenis"] == "Tambah":
                st.write(f"{idx}. {transaksi['tanggal']} - Tambah {transaksi['unit']} unit @ {transaksi['nilai']:.2f}")
            else:
                st.write(f"{idx}. {transaksi['tanggal']} - Kurang {transaksi['unit']} unit")
    else:
        st.info("Belum ada transaksi.")

    # Hitung Persediaan Akhir
    if st.button("Hitung Persediaan Akhir"):
        if st.session_state.inventory:
            inventory, total_unit, total_nilai = calculate_fifo(st.session_state.inventory, st.session_state.transactions)
            st.subheader("Hasil Perhitungan FIFO")
            st.write(f"Total Unit: {total_unit}")
            st.write(f"Total Nilai: {total_nilai:.2f}")
            st.write("Rincian Persediaan Akhir:")
            for item in inventory:
                st.write(f"- {item['unit']} unit @ {item['nilai']:.2f}")
        else:
            st.error("Saldo awal belum diset!")

    # Reset Aplikasi
    if st.button("Reset"):
        st.session_state.inventory.clear()
        st.session_state.transactions.clear()
        st.success("Aplikasi telah direset!")


# Jalankan halaman FIFO
if __name__ == "__main__":
    fifo_page()

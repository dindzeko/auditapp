import streamlit as st
from datetime import datetime

# Fungsi utama untuk menghitung FIFO secara Individu
def calculate_individu(inventory, transactions):
    inventory = inventory.copy()
    transactions = sorted(transactions, key=lambda x: x["tanggal"])
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
    
    # Input Transaksi
    st.subheader("Tambah/Kurang Persediaan")
    tanggal = st.date_input("Pilih Tanggal Transaksi", value=datetime.today())  # Date picker
    jenis_transaksi = st.selectbox("Jenis Transaksi", ["Tambah", "Kurang"])
    unit = st.number_input("Jumlah Unit", min_value=0, step=1)
    
    if jenis_transaksi == "Tambah":
        nilai_per_unit = st.number_input("Nilai Per Unit", min_value=0.0, step=0.01)
    else:
        nilai_per_unit = None
    
    if st.button("Tambahkan Transaksi"):
        if unit > 0:
            if jenis_transaksi == "Tambah" and nilai_per_unit > 0:
                st.session_state.transactions.append({
                    "tanggal": tanggal,
                    "unit": unit,
                    "nilai": nilai_per_unit,
                    "jenis": jenis_transaksi
                })
                st.success("Transaksi penambahan berhasil ditambahkan!")
            elif jenis_transaksi == "Kurang":
                st.session_state.transactions.append({
                    "tanggal": tanggal,
                    "unit": unit,
                    "jenis": jenis_transaksi
                })
                st.success("Transaksi pengurangan berhasil ditambahkan!")
            else:
                st.error("Masukkan data transaksi yang valid!")
        else:
            st.error("Jumlah unit harus lebih dari 0!")
    
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
            inventory, total_unit, total_nilai = calculate_individu(st.session_state.inventory, st.session_state.transactions)
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

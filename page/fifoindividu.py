import streamlit as st
from datetime import datetime

# Fungsi utama untuk menghitung FIFO secara Individu
def calculate_individu(inventory, transactions):
    inventory = inventory.copy()
    transactions = sorted(transactions, key=lambda x: x["tanggal"])
    for transaksi in transactions:
        if transaksi["Mutasi"] == "Tambah":
            inventory.append({"unit": transaksi["unit"], "nilai": transaksi["nilai"]})
        elif transaksi["Mutasi"] == "Kurang":
            unit_to_remove = transaksi["unit"]
            total_unit_inventory = sum(item["unit"] for item in inventory)
            
            # Validasi: Jika unit yang ingin dikurangi melebihi total unit yang tersedia
            if unit_to_remove > total_unit_inventory:
                return None  # Mengembalikan None jika transaksi gagal
            
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
def app():
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
    tanggal = st.date_input(
        "Pilih Tanggal Transaksi",
        value=datetime(2024, 1, 1),
        min_value=datetime(2024, 1, 1),
        max_value=datetime(2025, 4, 1)
    )
    mutasi_transaksi = st.selectbox("Mutasi Transaksi", ["Tambah", "Kurang"])
    unit = st.number_input("Jumlah Unit", min_value=0, step=1)
    
    if mutasi_transaksi == "Tambah":
        nilai_per_unit = st.number_input("Nilai Per Unit", min_value=0.0, step=0.01)
    else:
        nilai_per_unit = None
    
    if st.button("Tambahkan Transaksi"):
        if unit > 0:
            if mutasi_transaksi == "Tambah" and nilai_per_unit > 0:
                st.session_state.transactions.append({
                    "tanggal": tanggal,
                    "unit": unit,
                    "nilai": nilai_per_unit,
                    "Mutasi": mutasi_transaksi
                })
                st.success("Transaksi penambahan berhasil ditambahkan!")
            elif mutasi_transaksi == "Kurang":
                # Hitung total unit saat ini sebelum menambahkan transaksi
                result = calculate_individu(st.session_state.inventory, st.session_state.transactions)
                if result is None:
                    st.error("Terjadi kesalahan dalam perhitungan persediaan. Silakan coba lagi.")
                    return
                
                current_inventory, _, _ = result
                total_unit_inventory = sum(item["unit"] for item in current_inventory)
                
                if unit > total_unit_inventory:
                    st.error(f"Pengurangan {unit} unit melebihi total persediaan ({total_unit_inventory} unit). Transaksi dibatalkan.")
                else:
                    st.session_state.transactions.append({
                        "tanggal": tanggal,
                        "unit": unit,
                        "Mutasi": mutasi_transaksi
                    })
                    st.success("Transaksi pengurangan berhasil ditambahkan!")
            else:
                st.error("Masukkan data transaksi yang valid!")
        else:
            st.error("Jumlah unit harus lebih dari 0!")
    
    # Daftar Transaksi
    st.subheader("Daftar Transaksi")
    if st.session_state.transactions:
        for idx, transaksi in enumerate(st.session_state.transactions):
            col1, col2 = st.columns([4, 1])
            with col1:
                if transaksi["Mutasi"] == "Tambah":
                    st.write(f"{idx + 1}. {transaksi['tanggal']} - Tambah {transaksi['unit']} unit @ {transaksi['nilai']:.2f}")
                else:
                    st.write(f"{idx + 1}. {transaksi['tanggal']} - Kurang {transaksi['unit']} unit")
            with col2:
                if st.button(f"Hapus {idx}", key=f"hapus_{idx}"):
                    st.session_state.transactions.pop(idx)
                    st.rerun()
    else:
        st.info("Belum ada transaksi.")
    
    # Hitung Persediaan Akhir Secara Real-Time
    if st.session_state.inventory or st.session_state.transactions:
        result = calculate_individu(st.session_state.inventory, st.session_state.transactions)
        if result is None:
            st.error("Terjadi kesalahan dalam perhitungan persediaan. Silakan periksa transaksi Anda.")
        else:
            inventory, total_unit, total_nilai = result
            st.subheader("Posisi Persediaan Saat Ini")
            st.write(f"Total Unit: {total_unit}")
            st.write(f"Total Nilai: {total_nilai:.2f}")
            if inventory:
                st.write("Rincian Persediaan:")
                for item in inventory:
                    st.write(f"- {item['unit']} unit @ {item['nilai']:.2f}")
            else:
                st.warning("Persediaan kosong!")
    
    # Reset Aplikasi
    if st.button("Reset"):
        st.session_state.inventory.clear()
        st.session_state.transactions.clear()
        st.rerun()

# Jalankan halaman FIFO
if __name__ == "__main__":
    app()

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
            total_unit_inventory = sum(item["unit"] for item in inventory)
            
            # Validasi: Jika unit yang ingin dikurangi melebihi total unit yang tersedia
            if unit_to_remove > total_unit_inventory:
                st.error(f"Transaksi gagal! Pengurangan {unit_to_remove} unit melebihi total persediaan ({total_unit_inventory} unit).")
                return inventory, sum(item["unit"] for item in inventory), sum(item["unit"] * item["nilai"] for item in inventory)
            
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
    st.title("Rekalkulasi Perhitungan FIFO")
    
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
    # Set default tanggal ke 2024-01-01 dengan batasan minimal dan maksimal
    tanggal = st.date_input(
        "Pilih Tanggal Transaksi",
        value=datetime(2024, 1, 1),  # Default ke 1 Januari 2024
        min_value=datetime(2024, 1, 1),  # Minimal 1 Januari 2024
        max_value=datetime(2025, 4, 1)   # Maksimal 1 April 2025
    )
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
                # Hitung total unit saat ini sebelum menambahkan transaksi
                current_inventory, _, _ = calculate_individu(st.session_state.inventory, st.session_state.transactions)
                total_unit_inventory = sum(item["unit"] for item in current_inventory)
                
                if unit > total_unit_inventory:
                    st.error(f"Pengurangan {unit} unit melebihi total persediaan ({total_unit_inventory} unit). Transaksi dibatalkan.")
                else:
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
        for idx, transaksi in enumerate(st.session_state.transactions):
            col1, col2 = st.columns([4, 1])  # Kolom untuk detail transaksi dan tombol hapus
            with col1:
                if transaksi["jenis"] == "Tambah":
                    st.write(f"{idx + 1}. {transaksi['tanggal']} - Tambah {transaksi['unit']} unit @ {transaksi['nilai']:.2f}")
                else:
                    st.write(f"{idx + 1}. {transaksi['tanggal']} - Kurang {transaksi['unit']} unit")
            with col2:
                if st.button(f"Hapus {idx}", key=f"hapus_{idx}"):
                    st.session_state.transactions.pop(idx)
                    st.rerun()  # Gunakan st.rerun() untuk memuat ulang halaman
    else:
        st.info("Belum ada transaksi.")
    
    # Hitung Persediaan Akhir Secara Real-Time
    if st.session_state.inventory or st.session_state.transactions:
        inventory, total_unit, total_nilai = calculate_individu(st.session_state.inventory, st.session_state.transactions)
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
        # Bersihkan semua data di session state
        st.session_state.inventory.clear()
        st.session_state.transactions.clear()
        
        # Force reload halaman untuk memastikan reset penuh
        st.rerun()

# Jalankan halaman FIFO
if __name__ == "__main__":
    app()

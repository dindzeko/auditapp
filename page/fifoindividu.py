import streamlit as st
from datetime import datetime

def calculate_individu(inventory, transactions):
    inventory = [item.copy() for item in inventory]
    transactions = sorted(transactions, key=lambda x: x["tanggal"])
    total_beban = 0  # Variabel untuk menghitung total beban
    
    for transaksi in transactions:
        if transaksi["Mutasi"] == "Tambah":
            inventory.append({"unit": transaksi["unit"], "nilai": transaksi["nilai"]})
        elif transaksi["Mutasi"] == "Kurang":
            unit_to_remove = transaksi["unit"]
            total_unit_inventory = sum(item["unit"] for item in inventory)
            
            if unit_to_remove > total_unit_inventory:
                return None
            
            while unit_to_remove > 0 and inventory:
                oldest = inventory[0]
                if oldest["unit"] <= unit_to_remove:
                    # Hitung beban dari unit tertua
                    total_beban += oldest["unit"] * oldest["nilai"]
                    unit_to_remove -= oldest["unit"]
                    inventory.pop(0)
                else:
                    # Hitung beban dari sebagian unit tertua
                    total_beban += unit_to_remove * oldest["nilai"]
                    oldest["unit"] -= unit_to_remove
                    unit_to_remove = 0
    
    total_unit = sum(item["unit"] for item in inventory)
    total_nilai = sum(item["unit"] * item["nilai"] for item in inventory)
    return inventory, total_unit, total_nilai, total_beban

def app():
    if "inventory" not in st.session_state:
        st.session_state.inventory = []
    if "transactions" not in st.session_state:
        st.session_state.transactions = []
    
    st.subheader("Saldo Awal")
    saldo_unit = st.number_input("Jumlah Unit (Saldo Awal)", min_value=0, step=1)
    saldo_nilai = st.number_input("Nilai Per Unit (Saldo Awal)", min_value=0.0, step=0.01)
    
    if st.button("Set Saldo Awal"):
        if saldo_unit > 0 and saldo_nilai > 0:
            st.session_state.inventory = [{"unit": saldo_unit, "nilai": saldo_nilai}]
            st.success("Saldo awal berhasil diset!")
        else:
            st.error("Masukkan jumlah unit dan nilai per unit yang valid!")
    
    st.subheader("Tambah/Kurang Persediaan")
    tanggal = st.date_input(
        "Pilih Tanggal Transaksi",
        value=datetime(2024, 1, 1),
        min_value=datetime(2024, 1, 1),
        max_value=datetime(2025, 4, 1)
    )
    mutasi_transaksi = st.selectbox("Mutasi Transaksi", ["Tambah", "Kurang"])
    unit = st.number_input("Jumlah Unit", min_value=0, step=1)
    
    nilai_per_unit = None
    if mutasi_transaksi == "Tambah":
        nilai_per_unit = st.number_input("Nilai Per Unit", min_value=0.0, step=0.01)
    
    if st.button("Tambahkan Transaksi"):
        if unit <= 0:
            st.error("Jumlah unit harus lebih dari 0!")
            return
        
        new_trans = {
            "tanggal": tanggal,
            "unit": unit,
            "Mutasi": mutasi_transaksi
        }
        if mutasi_transaksi == "Tambah":
            if nilai_per_unit <= 0:
                st.error("Nilai per unit harus lebih dari 0!")
                return
            new_trans["nilai"] = nilai_per_unit
            st.session_state.transactions.append(new_trans)
            st.success("Transaksi penambahan berhasil ditambahkan!")
        else:
            temp_trans = st.session_state.transactions.copy()
            temp_trans.append(new_trans)
            result = calculate_individu(st.session_state.inventory, temp_trans)
            if result is None:
                st.error(f"Pengurangan {unit} unit tidak valid (melebihi persediaan).")
            else:
                st.session_state.transactions.append(new_trans)
                st.success("Transaksi pengurangan berhasil ditambahkan!")
    
    st.subheader("Daftar Transaksi")
    if st.session_state.inventory:
        st.write("#### Saldo Awal:")
        saldo_awal = st.session_state.inventory[0]
        st.write(f"- {saldo_awal['unit']} unit @ {saldo_awal['nilai']:.2f}")
    
    if st.session_state.transactions:
        st.write("#### Mutasi Transaksi:")
        for idx, trans in enumerate(st.session_state.transactions):
            if trans["Mutasi"] == "Tambah":
                st.write(f"{idx + 1}. Tambah - {trans['unit']} unit @ {trans.get('nilai', 0):.2f} pada {trans['tanggal']}")
            elif trans["Mutasi"] == "Kurang":
                st.write(f"{idx + 1}. Kurang - {trans['unit']} unit pada {trans['tanggal']}")
            
            if st.button(f"Hapus Transaksi {idx + 1}", key=f"delete_{idx}"):
                st.session_state.transactions.pop(idx)
                st.rerun()
    else:
        st.write("Belum ada transaksi.")
    
    st.subheader("Proses Hitung FIFO")
    if st.button("Proses Hitung"):
        if not st.session_state.inventory:
            st.error("Silakan set saldo awal terlebih dahulu!")
            return
        result = calculate_individu(st.session_state.inventory, st.session_state.transactions)
        if result is None:
            st.error("Transaksi tidak valid: pengurangan melebihi stok yang tersedia.")
        else:
            inventory, total_unit, total_nilai, total_beban = result
            st.subheader("Hasil Perhitungan FIFO")
            st.write(f"Total Unit: {total_unit}")
            st.write(f"Total Nilai: {total_nilai:.2f}")
            st.write(f"Total Beban Persediaan: {total_beban:.2f}")  # Tampilkan total beban
            if inventory:
                for item in inventory:
                    st.write(f"- {item['unit']} unit @ {item['nilai']:.2f}")
            else:
                st.warning("Persediaan kosong!")
    
    if st.button("Reset"):
        st.session_state.inventory = []
        st.session_state.transactions = []
        st.rerun()

if __name__ == "__main__":
    app()

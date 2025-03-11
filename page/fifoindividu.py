import streamlit as st
from datetime import datetime

def calculate_fifo(inventory, transactions):
    inventory = [item.copy() for item in inventory]
    transactions = sorted(transactions, key=lambda x: x["tanggal"])
    total_beban = 0
    
    for trans in transactions:
        if trans["Mutasi"] == "Tambah":
            inventory.append({"unit": trans["unit"], "nilai": trans["nilai"]})
        elif trans["Mutasi"] == "Kurang":
            unit_needed = trans["unit"]
            
            while unit_needed > 0 and inventory:
                oldest = inventory[0]
                if oldest["unit"] <= unit_needed:
                    total_beban += oldest["unit"] * oldest["nilai"]
                    unit_needed -= oldest["unit"]
                    inventory.pop(0)
                else:
                    total_beban += unit_needed * oldest["nilai"]
                    oldest["unit"] -= unit_needed
                    unit_needed = 0
    
    return total_beban

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
            st.error("Unit dan nilai harus lebih dari 0!")
    
    st.subheader("Tambah/Kurang Persediaan")
    tanggal = st.date_input(
        "Tanggal Transaksi",
        value=datetime(2024, 1, 1),
        min_value=datetime(2024, 1, 1),
        max_value=datetime(2025, 4, 1)
    )
    mutasi = st.selectbox("Jenis Transaksi", ["Tambah", "Kurang"])
    unit = st.number_input("Jumlah Unit", min_value=1, step=1)
    
    if mutasi == "Tambah":
        nilai = st.number_input("Nilai Per Unit", min_value=0.01, step=0.01)
    
    if st.button("Tambahkan Transaksi"):
        new_trans = {
            "tanggal": tanggal,
            "unit": unit,
            "Mutasi": mutasi
        }
        
        if mutasi == "Tambah":
            if nilai <= 0:
                st.error("Nilai per unit harus lebih dari 0!")
                return
            new_trans["nilai"] = nilai
        
        # Validasi transaksi sebelum ditambahkan
        dummy_inventory = [item.copy() for item in st.session_state.inventory]
        temp_trans = st.session_state.transactions.copy()
        temp_trans.append(new_trans)
        valid = True
        
        for trans in temp_trans:
            if trans["Mutasi"] == "Kurang":
                available = sum(item["unit"] for item in dummy_inventory)
                if trans["unit"] > available:
                    valid = False
                    break
                # Simulasi pengurangan
                unit_needed = trans["unit"]
                while unit_needed > 0:
                    oldest = dummy_inventory[0]
                    if oldest["unit"] <= unit_needed:
                        unit_needed -= oldest["unit"]
                        dummy_inventory.pop(0)
                    else:
                        oldest["unit"] -= unit_needed
                        unit_needed = 0
        
        if valid:
            st.session_state.transactions.append(new_trans)
            st.success(f"Transaksi {mutasi} {unit} unit berhasil ditambahkan!")
        else:
            st.error("Transaksi pengurangan melebihi stok yang tersedia!")
    
    st.subheader("Proses Perhitungan FIFO")
    if st.button("Hitung Total Beban"):
        if not st.session_state.inventory:
            st.error("Saldo awal belum diatur!")
            return
        
        total_beban = calculate_fifo(st.session_state.inventory, st.session_state.transactions)
        st.subheader("Hasil Perhitungan")
        st.write(f"**Total Beban Persediaan: {total_beban:,.2f}**")

    if st.button("Reset"):
        st.session_state.inventory = []
        st.session_state.transactions = []
        st.rerun()

if __name__ == "__main__":
    app()

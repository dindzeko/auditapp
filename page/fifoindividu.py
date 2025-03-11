import streamlit as st
from datetime import datetime

def calculate_fifo(inventory, transactions):
    inventory = [item.copy() for item in inventory]  # Deep copy
    transactions = sorted(transactions, key=lambda x: x["tanggal"])
    total_beban = 0  # Untuk menghitung total beban
    
    for trans in transactions:
        if trans["Mutasi"] == "Tambah":
            inventory.append({"unit": trans["unit"], "nilai": trans["nilai"]})
        elif trans["Mutasi"] == "Kurang":
            unit_needed = trans["unit"]
            
            while unit_needed > 0 and inventory:
                oldest = inventory[0]
                if oldest["unit"] <= unit_needed:
                    # Hitung beban dari unit tertua
                    total_beban += oldest["unit"] * oldest["nilai"]
                    unit_needed -= oldest["unit"]
                    inventory.pop(0)
                else:
                    # Ambil sebagian dari unit tertua
                    total_beban += unit_needed * oldest["nilai"]
                    oldest["unit"] -= unit_needed
                    unit_needed = 0
    
    total_unit = sum(item["unit"] for item in inventory)
    total_nilai = sum(item["unit"] * item["nilai"] for item in inventory)
    
    return {
        "inventory": inventory,
        "total_unit": total_unit,
        "total_nilai": total_nilai,
        "total_beban": total_beban
    }

def app():
    # Inisialisasi session state
    if "inventory" not in st.session_state:
        st.session_state.inventory = []
    if "transactions" not in st.session_state:
        st.session_state.transactions = []
    
    # --- Saldo Awal ---
    st.subheader("Saldo Awal")
    saldo_unit = st.number_input("Jumlah Unit (Saldo Awal)", min_value=0, step=1)
    saldo_nilai = st.number_input("Nilai Per Unit (Saldo Awal)", min_value=0.0, step=0.01)
    
    if st.button("Set Saldo Awal"):
        if saldo_unit > 0 and saldo_nilai > 0:
            st.session_state.inventory = [{"unit": saldo_unit, "nilai": saldo_nilai}]
            st.success(f"Saldo awal {saldo_unit} unit @ {saldo_nilai:.2f} berhasil diset!")
        else:
            st.error("Unit dan nilai harus lebih dari 0!")
    
    # --- Transaksi ---
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
        
        # Validasi pengurangan
        temp_trans = st.session_state.transactions.copy()
        temp_trans.append(new_trans)
        result = calculate_fifo(st.session_state.inventory, temp_trans)
        
        if result is None:
            st.error("Transaksi pengurangan melebihi stok!")
        else:
            st.session_state.transactions.append(new_trans)
            st.success(f"Transaksi {mutasi} {unit} unit berhasil ditambahkan!")
    
    # --- Daftar Transaksi ---
    st.subheader("Daftar Transaksi")
    if st.session_state.inventory:
        st.write(f"**Saldo Awal:** {st.session_state.inventory[0]['unit']} unit @ {st.session_state.inventory[0]['nilai']:.2f}")
    
    if st.session_state.transactions:
        st.write("**Mutasi:**")
        for idx, trans in enumerate(st.session_state.transactions):
            tipe = "Tambah" if trans["Mutasi"] == "Tambah" else "Kurang"
            detail = f"{trans['unit']} unit"
            
            if trans["Mutasi"] == "Tambah":
                detail += f" @ {trans['nilai']:.2f}"
            
            st.write(f"{idx+1}. {tipe} - {detail} ({trans['tanggal']})")
            
            # Tombol hapus
            if st.button(f"❌ Hapus {idx+1}", key=f"del_{idx}"):
                st.session_state.transactions.pop(idx)
                st.rerun()
    else:
        st.info("Belum ada transaksi.")
    
    # --- Proses Hitung ---
    st.subheader("Proses Perhitungan FIFO")
    if st.button("Hitung FIFO"):
        if not st.session_state.inventory:
            st.error("Saldo awal belum diatur!")
            return
        
        result = calculate_fifo(st.session_state.inventory, st.session_state.transactions)
        
        if result["total_unit"] < 0:
            st.error("Transaksi tidak valid: stok tidak mencukupi!")
        else:
            st.subheader("Hasil Perhitungan")
            st.write(f"**Total Unit Tersisa:** {result['total_unit']}")
            st.write(f"**Total Nilai Persediaan:** {result['total_nilai']:.2f}")
            st.write(f"**Total Beban Persediaan:** {result['total_beban']:.2f}")
            
            if result['inventory']:
                st.write("**Rincian Persediaan:**")
                for item in result['inventory']:
                    st.write(f"- {item['unit']} unit @ {item['nilai']:.2f}")
            else:
                st.warning("Persediaan kosong!")

    # --- Reset ---
    if st.button("Reset Semua"):
        st.session_state.inventory = []
        st.session_state.transactions = []
        st.rerun()

if __name__ == "__main__":
    app()

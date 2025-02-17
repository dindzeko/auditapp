import streamlit as st

def app():
    # Judul aplikasi
    st.title("Persediaan Akhir dengan Metode FIFO")

    # Data transaksi
    if 'inventory' not in st.session_state:
        st.session_state.inventory = []  # Format: [{"type": "purchase/sale", "quantity": int, "price": float}]

    # Fungsi untuk menambahkan pembelian
    def add_purchase(quantity, price):
        if quantity > 0 and price > 0:
            st.session_state.inventory.append({"type": "purchase", "quantity": quantity, "price": price})
            st.success(f"Pembelian {quantity} unit @ {price} berhasil ditambahkan.")
        else:
            st.error("Masukkan jumlah barang dan harga yang valid.")

    # Fungsi untuk menambahkan penjualan
    def add_sale(quantity):
        if quantity > 0:
            st.session_state.inventory.append({"type": "sale", "quantity": quantity})
            st.success(f"Penjualan {quantity} unit berhasil ditambahkan.")
        else:
            st.error("Masukkan jumlah barang yang valid.")

    # Fungsi untuk menghitung persediaan akhir dengan metode FIFO
    def calculate_fifo():
        stock = []
        total_cost = 0
        total_units = 0

        for transaction in st.session_state.inventory:
            if transaction["type"] == "purchase":
                # Tambahkan pembelian ke stok
                stock.append({"quantity": transaction["quantity"], "price": transaction["price"]})
                total_units += transaction["quantity"]
                total_cost += transaction["quantity"] * transaction["price"]
            elif transaction["type"] == "sale":
                sale_quantity = transaction["quantity"]
                while sale_quantity > 0 and stock:
                    oldest = stock[0]
                    if oldest["quantity"] <= sale_quantity:
                        # Jika stok pertama habis terjual
                        sale_quantity -= oldest["quantity"]
                        total_units -= oldest["quantity"]
                        total_cost -= oldest["quantity"] * oldest["price"]
                        stock.pop(0)
                    else:
                        # Jika hanya sebagian dari stok pertama yang terjual
                        oldest["quantity"] -= sale_quantity
                        total_units -= sale_quantity
                        total_cost -= sale_quantity * oldest["price"]
                        sale_quantity = 0

        # Menampilkan hasil
        st.subheader("Persediaan Akhir:")
        st.write("Batch Persediaan:")
        for i, item in enumerate(stock):
            st.write(f"Batch {i+1}: {item['quantity']} unit @ {item['price']}")
        st.write(f"Total Unit: {total_units}")
        st.write(f"Total Biaya: {total_cost:.2f}")

    # Input untuk pembelian
    st.header("Transaksi Pembelian")
    purchase_quantity = st.number_input("Jumlah Barang (Pembelian)", min_value=0, step=1)
    purchase_price = st.number_input("Harga per Unit (Pembelian)", min_value=0.0, step=0.01)
    if st.button("Tambah Pembelian"):
        add_purchase(purchase_quantity, purchase_price)

    # Input untuk penjualan
    st.header("Transaksi Penjualan")
    sale_quantity = st.number_input("Jumlah Barang (Penjualan)", min_value=0, step=1)
    if st.button("Tambah Penjualan"):
        add_sale(sale_quantity)

    # Tombol untuk menghitung persediaan akhir
    st.header("Hitung Persediaan Akhir")
    if st.button("Hitung Persediaan Akhir"):
        calculate_fifo()

# Jalankan aplikasi Streamlit
if __name__ == "__main__":
    app()

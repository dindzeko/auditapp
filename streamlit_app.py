def measurement():
    st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
    st.title("Measurement")
    st.write("Halaman untuk menghitung luas area berdasarkan gambar atau image.")
    
    # Upload gambar
    uploaded_file = st.file_uploader("Upload Gambar", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        st.image(uploaded_file, caption="Gambar yang Diupload", use_column_width=True)
        st.success("Gambar berhasil diupload!")

        # Input skala referensi
        reference_length = st.number_input("Masukkan panjang garis referensi (dalam meter):", value=1.0)
        if st.button("Hitung Skala"):
            st.success(f"Skala ditentukan: {reference_length} meter per piksel")

        # Input poligon
        st.write("Gambar poligon pada gambar untuk menghitung luas dan panjang total.")
        if st.button("Hitung Luas dan Panjang"):
            st.info("Fitur ini sedang dikembangkan. Silakan coba lagi nanti!")

    st.markdown('</div>', unsafe_allow_html=True)

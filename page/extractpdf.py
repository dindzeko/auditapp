def app():
    st.title("📚 Ekstrak Halaman PDF")
    st.markdown("""
    Aplikasi ini memungkinkan Anda mengekstrak halaman tertentu dari file PDF.
    Anda dapat memasukkan rentang halaman (contoh: `6-12`) atau daftar halaman individu (contoh: `8,9,12`).
    """)
    
    # Upload file PDF
    uploaded_file = st.file_uploader("📂 Pilih File PDF", type="pdf")
    
    # Input untuk halaman yang ingin diekstrak
    page_input = st.text_input("📄 Halaman (contoh: 6-12 atau 8,9,12):")
    
    # Tombol Proses
    if st.button("🚀 Proses"):
        if not uploaded_file:
            st.error("⚠️ Silakan unggah file PDF terlebih dahulu!")
        elif not page_input.strip():
            st.error("⚠️ Masukkan halaman yang ingin diekstrak (contoh: 6-12 atau 8,9,12)!")
        else:
            # Simpan file yang diupload ke direktori sementara
            temp_file_path = os.path.join("/tmp", uploaded_file.name)
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Proses ekstraksi halaman
            output_path = extractpdf(temp_file_path, page_input)
            if output_path:
                # Tampilkan link untuk mendownload file hasil ekstraksi
                with open(output_path, "rb") as file:
                    st.success("✅ Halaman berhasil diekstrak!")
                    st.download_button(
                        label="📥 Download File Hasil Ekstraksi",
                        data=file,
                        file_name=os.path.basename(output_path),
                        mime="application/pdf"
                    )
                # Bersihkan file sementara
                os.remove(temp_file_path)
                os.remove(output_path)

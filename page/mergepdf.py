import os
import streamlit as st
from pypdf import PdfReader, PdfWriter

# Fungsi untuk menggabungkan beberapa file PDF menjadi satu
def merge_pdfs(pdf_files, output_pdf):
    writer = PdfWriter()
    try:
        for pdf_file in pdf_files:
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                writer.add_page(page)
        # Simpan file PDF hasil penggabungan
        with open(output_pdf, "wb") as output_file:
            writer.write(output_file)
        st.success(f"File PDF berhasil digabungkan sebagai {output_pdf}")
    except Exception as e:
        st.error(f"Gagal menggabungkan PDF: {str(e)}")

# Fungsi utama untuk halaman Streamlit
def app():
    st.title("Penggabung PDF")
    st.markdown("### Gabungkan beberapa file PDF menjadi satu file.")

    # Upload file PDF
    uploaded_files = st.file_uploader(
        "Pilih file PDF yang ingin digabungkan",
        type="pdf",
        accept_multiple_files=True
    )

    # Input untuk nama file output
    output_file_name = st.text_input(
        "Nama file output (contoh: hasil_gabungan.pdf)",
        value="hasil_gabungan.pdf"
    )

    # Tombol untuk memulai proses penggabungan
    if st.button("Gabungkan"):
        if not uploaded_files:
            st.error("Tidak ada file PDF yang dipilih!")
        elif not output_file_name.strip():
            st.error("Masukkan nama file output!")
        else:
            # Simpan file yang diupload ke direktori sementara
            temp_files = []
            for uploaded_file in uploaded_files:
                temp_file_path = os.path.join("/tmp", uploaded_file.name)
                with open(temp_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                temp_files.append(temp_file_path)

            # Tentukan path untuk file output
            output_path = os.path.join("/tmp", output_file_name)

            # Proses penggabungan PDF
            merge_pdfs(temp_files, output_path)

            # Tampilkan link untuk mendownload file hasil gabungan
            with open(output_path, "rb") as file:
                st.download_button(
                    label="Download File Hasil Gabungan",
                    data=file,
                    file_name=output_file_name,
                    mime="application/pdf"
                )

            # Bersihkan file sementara
            for temp_file in temp_files:
                os.remove(temp_file)
            os.remove(output_path)

# Jalankan aplikasi Streamlit
if __name__ == "__main__":
    app()

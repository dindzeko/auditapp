import os
import streamlit as st
from pypdf import PdfReader, PdfWriter

# Fungsi untuk mengekstrak halaman tertentu dari PDF
def extractpdf(input_pdf, page_input):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    pages = []
    try:
        # Parsing input halaman
        for part in page_input.split(","):
            if "-" in part:  # Rentang halaman (contoh: 6-12)
                start, end = map(int, part.split("-"))
                if start < 1 or end > len(reader.pages) or start > end:
                    raise ValueError(f"Rentang halaman {part} tidak valid!")
                pages.extend(range(start, end + 1))
            else:  # Halaman tunggal (contoh: 8)
                page = int(part.strip())
                if page < 1 or page > len(reader.pages):
                    raise ValueError(f"Halaman {page} tidak valid!")
                pages.append(page)
    except ValueError as e:
        st.error(str(e))
        return None

    # Hapus duplikat dan urutkan halaman
    pages = sorted(set(pages))

    # Buat nama file output berdasarkan dua angka awal dan dua angka akhir
    if pages:
        first_page = pages[0]
        last_page = pages[-1]
        output_pdf = f"pages_{first_page:02d}_to_{last_page:02d}.pdf"
    else:
        st.error("Tidak ada halaman yang valid untuk diekstrak!")
        return None

    # Tambahkan halaman ke writer
    for page_num in pages:
        writer.add_page(reader.pages[page_num - 1])  # Halaman dimulai dari indeks 0

    # Simpan file PDF hasil ekstraksi
    output_path = os.path.join("/tmp", output_pdf)
    with open(output_path, "wb") as output_file:
        writer.write(output_file)

    return output_path

# Fungsi utama untuk halaman Streamlit
def app():
    # Judul dan deskripsi
    st.title("📚 Ekstrak Halaman PDF")
    st.markdown("""
    Aplikasi ini memungkinkan Anda mengekstrak halaman tertentu dari file PDF.
    Anda dapat memasukkan rentang halaman (contoh: `6-12`) atau daftar halaman individu (contoh: `8,9,12`).
    """)

    # Sidebar untuk navigasi dan informasi tambahan
    with st.sidebar:
        st.header("📝 Panduan Penggunaan")
        st.markdown("""
        1. Unggah file PDF yang ingin Anda ekstrak.
        2. Masukkan nomor halaman yang ingin diekstrak:
           - Gunakan tanda koma (`,`) untuk memisahkan halaman individu.
           - Gunakan tanda hubung (`-`) untuk menentukan rentang halaman.
        3. Klik tombol **Proses** untuk mengekstrak halaman.
        4. Unduh file hasil ekstraksi.
        """)
        st.info("Contoh input halaman: `6-12` atau `8,9,12`")

    # Layout utama
    col1, col2 = st.columns([2, 1])

    with col1:
        # Upload file PDF
        uploaded_file = st.file_uploader(
            "📂 Pilih File PDF",
            type="pdf",
            help="Unggah file PDF yang ingin Anda ekstrak."
        )

    with col2:
        # Input untuk halaman yang ingin diekstrak
        page_input = st.text_input(
            "📄 Halaman (contoh: 6-12 atau 8,9,12):",
            value="",
            help="Masukkan nomor halaman yang ingin diekstrak."
        )

    # Tombol Proses
    if st.button("🚀 Proses", use_container_width=True):
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
                        mime="application/pdf",
                        use_container_width=True
                    )

                # Bersihkan file sementara
                os.remove(temp_file_path)
                os.remove(output_path)

# Jalankan aplikasi Streamlit
if __name__ == "__main__":
    app()

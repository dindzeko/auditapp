import streamlit as st
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import re
import io

def app():
    st.write("Upload dokumen Word (.docx) untuk merekalkulasi tabel.")

    uploaded_file = st.file_uploader("Upload File Word (.docx)", type=["docx"])

    if uploaded_file is not None:
        try:
            # Baca dokumen
            doc = Document(uploaded_file)
            
            with st.spinner("Memproses dokumen..."):
                recalculate_tables(doc)
                
                # Simpan ke memori
                output = io.BytesIO()
                doc.save(output)
                output.seek(0)

            st.success("Rekalkulasi selesai!")
            st.download_button(
                label="📥 Unduh Hasil",
                data=output,
                file_name="hasil_rekalkulasi.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

        except Exception as e:
            st.error(f"Terjadi kesalahan: {str(e)}")
            st.error("Pastikan file yang diupload adalah dokumen Word (.docx) valid")

def recalculate_tables(doc):
    # Daftar kata kunci untuk mendeteksi baris total/jumlah
    TOTAL_KEYWORDS = ["JUMLAH", "TOTAL", "SUM"]

    for table in doc.tables:
        if len(table.columns) < 3:
            continue  # Lewati tabel dengan kolom < 3

        num_cols = len(table.columns)
        vertical_sums = [0.0] * num_cols

        for row in table.rows:
            # Deteksi baris total
            is_total_row = (
                len(row.cells) > 0 and any(keyword in row.cells[0].text.upper() for keyword in TOTAL_KEYWORDS)
            )

            if is_total_row:
                continue

            # Proses kolom numerik (mulai dari kolom ke-3)
            for col_idx in range(2, num_cols):
                if col_idx >= len(row.cells):
                    continue

                cell_text = row.cells[col_idx].text.strip().replace('.', '').replace(',', '.')

                # Konversi ke angka
                try:
                    if cell_text in ['-', '']:
                        num = 0.0
                    elif re.match(r'^-?\d+\.?\d*$', cell_text):
                        num = float(cell_text)
                    elif re.match(r'^\(\d+\.?\d*\)$', cell_text):
                        num = -float(cell_text[1:-1])
                    else:
                        continue  # Lewati jika format tidak dikenali

                    vertical_sums[col_idx] += num

                except ValueError:
                    continue  # Lewati jika konversi gagal

        # Tambahkan baris rekalkulasi
        if any(vertical_sums[2:]):  # Hanya tambah jika ada data
            new_row = table.add_row()
            new_row.cells[0].text = "Rekalkulasi Sistem"

            for col_idx in range(num_cols):
                cell = new_row.cells[col_idx]
                if col_idx >= 2 and vertical_sums[col_idx] != 0:
                    formatted_num = format_number(vertical_sums[col_idx])
                    cell.text = formatted_num
                    set_cell_style(cell)

def format_number(number):
    return f"{number:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def set_cell_style(cell):
    for paragraph in cell.paragraphs:
        paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
        for run in paragraph.runs:
            run.font.name = 'Calibri'
            run.font.size = Pt(11)
            run.font.color.rgb = RGBColor(255, 0, 0)
            run.bold = True

if __name__ == "__main__":
    app()

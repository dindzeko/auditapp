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
            doc = Document(uploaded_file)
            with st.spinner("Memproses dokumen..."):
                recalculate_tables(doc)
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
    TOTAL_KEYWORDS = ["JUMLAH", "TOTAL", "SUM"]

    for table in doc.tables:
        # Deteksi kolom numerik secara dinamis
        numeric_cols = detect_numeric_columns(table)
        if not numeric_cols:
            continue  # Lewati tabel tanpa kolom numerik

        vertical_sums = [0.0] * len(table.columns)

        for row in table.rows:
            # Normalisasi teks untuk deteksi baris total (hapus spasi, case-insensitive)
            is_total_row = any(
                re.fullmatch(re.escape(keyword), cell.text.replace(" ", "").strip(), re.IGNORECASE)
                for cell in row.cells
                for keyword in TOTAL_KEYWORDS
            )

            if is_total_row:
                continue  # Lewati baris total

            # Proses kolom numerik yang terdeteksi
            for col_idx in numeric_cols:
                if col_idx >= len(row.cells):
                    continue

                cell_text = row.cells[col_idx].text.strip().replace('.', '').replace(',', '.')

                try:
                    if cell_text in ['-', '']:
                        num = 0.0
                    elif re.match(r'^-?\d+\.?\d*$', cell_text):
                        num = float(cell_text)
                    elif re.match(r'^\(\d+\.?\d*\)$', cell_text):
                        num = -float(cell_text[1:-1])
                    else:
                        continue  # Lewati format tidak dikenali

                    vertical_sums[col_idx] += num

                except ValueError:
                    continue  # Lewati konversi gagal

        # Tambahkan baris rekalkulasi
        if any(vertical_sums[col] != 0 for col in numeric_cols):
            new_row = table.add_row()
            new_row.cells[0].text = "Rekalkulasi Sistem"

            for col_idx in range(len(table.columns)):
                cell = new_row.cells[col_idx]
                if col_idx in numeric_cols and vertical_sums[col_idx] != 0:
                    formatted_num = format_number(vertical_sums[col_idx])
                    cell.text = formatted_num
                    set_cell_style(cell)

def detect_numeric_columns(table, sample_rows=3):
    """Deteksi kolom numerik berdasarkan sampel baris data"""
    if not table.rows:
        return []

    numeric_cols = []
    header_row = table.rows[0]

    # Ambil sampel baris data (hindari header dan total)
    data_rows = []
    for row in table.rows[1:]:
        # Normalisasi teks untuk deteksi baris total (hapus spasi, case-insensitive)
        if not any(
            re.fullmatch(re.escape(keyword), cell.text.replace(" ", "").strip(), re.IGNORECASE)
            for cell in row.cells
            for keyword in ["JUMLAH", "TOTAL", "SUM"]
        ):
            data_rows.append(row)
            if len(data_rows) >= sample_rows:
                break

    # Deteksi kolom numerik
    for col_idx in range(len(table.columns)):
        numeric_count = 0
        for row in data_rows:
            if col_idx >= len(row.cells):
                continue
            cell_text = row.cells[col_idx].text.strip().replace('.', '').replace(',', '.')
            if re.match(r'^-?\d+\.?\d*$', cell_text) or re.match(r'^\(\d+\.?\d*\)$', cell_text):
                numeric_count += 1
        if numeric_count > 0:
            numeric_cols.append(col_idx)

    return numeric_cols

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

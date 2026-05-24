import streamlit as st
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import re
import io


# =========================================================
# STREAMLIT APP
# =========================================================

def app():
    st.set_page_config(
        page_title="Verifikasi Footing Tabel Word",
        page_icon="📄",
        layout="wide"
    )

    st.title("📄 Verifikasi Footing Tabel Word")

    st.write(
        """
        Upload dokumen Word `.docx`. Aplikasi akan mengecek penjumlahan tabel,
        terutama baris `Jumlah`, `JUMLAH`, `Total`, dan `TOTAL`.
        """
    )

    st.info(
        """
        Tanda hasil pemeriksaan:
        - `^` hijau = sesuai.
        - `X` merah = berbeda dengan hasil rekalkulasi.
        """
    )

    st.caption(
        """
        Versi ini dibuat lebih ringan agar tidak muter-muter:
        deteksi subtotal otomatis yang berat dimatikan.
        """
    )

    col1, col2 = st.columns(2)

    with col1:
        tambah_baris_rekalkulasi = st.checkbox(
            "Jika tidak ada baris Jumlah/Total, tambahkan baris Rekalkulasi Sistem",
            value=False
        )

    with col2:
        tampilkan_debug = st.checkbox(
            "Tampilkan ringkasan proses",
            value=True
        )

    uploaded_file = st.file_uploader(
        "Upload File Word (.docx)",
        type=["docx"]
    )

    if uploaded_file is not None:
        try:
            doc = Document(uploaded_file)

            progress = st.progress(0)
            status_text = st.empty()

            with st.spinner("Memproses dokumen..."):
                summary = recalculate_tables(
                    doc=doc,
                    tambah_baris_rekalkulasi=tambah_baris_rekalkulasi,
                    progress=progress,
                    status_text=status_text
                )

                output = io.BytesIO()
                doc.save(output)
                output.seek(0)

            st.success("Rekalkulasi selesai!")

            if tampilkan_debug:
                st.subheader("Ringkasan Proses")
                st.json(summary)

            nama_file_hasil = buat_nama_file_hasil(uploaded_file.name)

            st.download_button(
                label="📥 Unduh Hasil Rekalkulasi",
                data=output,
                file_name=nama_file_hasil,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

        except Exception as e:
            st.error(f"Terjadi kesalahan: {str(e)}")
            st.error("Pastikan file yang diupload adalah dokumen Word `.docx` valid.")


def buat_nama_file_hasil(nama_file_upload):
    if not nama_file_upload:
        return "hasil_Rekalkulasi.docx"

    if nama_file_upload.lower().endswith(".docx"):
        nama_file_tanpa_ext = nama_file_upload[:-5]
    else:
        nama_file_tanpa_ext = nama_file_upload

    return f"{nama_file_tanpa_ext}_Rekalkulasi.docx"


# =========================================================
# MAIN PROCESS
# =========================================================

def recalculate_tables(doc, tambah_baris_rekalkulasi=False, progress=None, status_text=None):
    summary = {
        "jumlah_tabel": len(doc.tables),
        "tabel_diproses": 0,
        "tabel_tanpa_kolom_numerik": 0,
        "baris_total_biasa_ditemukan": 0,
        "baris_total_per_kelompok_ditemukan": 0,
        "baris_rekalkulasi_ditambahkan": 0,
        "sel_verified": 0,
        "sel_berbeda": 0,
        "detail_tabel": []
    }

    total_tables = len(doc.tables)

    for table_idx, table in enumerate(doc.tables, start=1):
        if progress is not None and total_tables > 0:
            progress.progress(table_idx / total_tables)

        if status_text is not None:
            status_text.write(f"Memproses tabel {table_idx} dari {total_tables}...")

        if not table.rows:
            continue

        clean_table_old_marks(table)

        numeric_cols = detect_numeric_columns_for_footing(table)

        detail = {
            "tabel": table_idx,
            "jumlah_baris": len(table.rows),
            "jumlah_kolom": len(table.columns),
            "numeric_cols": [c + 1 for c in numeric_cols],
            "status": ""
        }

        if not numeric_cols:
            summary["tabel_tanpa_kolom_numerik"] += 1
            detail["status"] = "Dilewati, tidak ada kolom numerik"
            summary["detail_tabel"].append(detail)
            continue

        summary["tabel_diproses"] += 1

        total_indices = find_total_row_indices(table)

        # =================================================
        # MODEL 1:
        # Tabel gabungan dalam satu tabel Word.
        # Contoh:
        # PT AJA
        # data...
        # Jumlah
        # CV DNM
        # data...
        # Jumlah
        # =================================================

        if len(total_indices) > 1:
            result_group = verify_total_rows_by_group(
                table=table,
                numeric_cols=numeric_cols
            )

            summary["baris_total_per_kelompok_ditemukan"] += result_group["total_rows"]
            summary["sel_verified"] += result_group["verified"]
            summary["sel_berbeda"] += result_group["different"]

            detail["status"] = "Diproses sebagai tabel gabungan per kelompok"
            detail["baris_total_per_kelompok"] = result_group["total_rows"]
            detail["verified"] = result_group["verified"]
            detail["different"] = result_group["different"]
            summary["detail_tabel"].append(detail)
            continue

        # =================================================
        # MODEL 2:
        # Tabel biasa, hanya satu baris Jumlah/Total.
        # =================================================

        if len(total_indices) == 1:
            total_row_idx = total_indices[0]

            vertical_sums = calculate_sums_between_rows(
                table=table,
                start_row_idx=0,
                end_row_idx=total_row_idx,
                numeric_cols=numeric_cols
            )

            result = verify_total_row(
                total_row=table.rows[total_row_idx],
                numeric_cols=numeric_cols,
                vertical_sums=vertical_sums
            )

            summary["baris_total_biasa_ditemukan"] += 1
            summary["sel_verified"] += result["verified"]
            summary["sel_berbeda"] += result["different"]

            detail["status"] = "Diproses sebagai tabel total biasa"
            detail["baris_total"] = total_row_idx + 1
            detail["verified"] = result["verified"]
            detail["different"] = result["different"]
            summary["detail_tabel"].append(detail)
            continue

        # =================================================
        # MODEL 3:
        # Tidak ada baris Jumlah/Total.
        # Jika user mau, tambahkan baris Rekalkulasi Sistem.
        # =================================================

        if len(total_indices) == 0:
            if tambah_baris_rekalkulasi:
                vertical_sums = calculate_sums_between_rows(
                    table=table,
                    start_row_idx=0,
                    end_row_idx=len(table.rows),
                    numeric_cols=numeric_cols
                )

                added = add_recalculation_row(
                    table=table,
                    numeric_cols=numeric_cols,
                    vertical_sums=vertical_sums
                )

                if added:
                    summary["baris_rekalkulasi_ditambahkan"] += 1
                    detail["status"] = "Tidak ada total, ditambahkan baris Rekalkulasi Sistem"
                else:
                    detail["status"] = "Tidak ada total dan tidak ada angka untuk direkalkulasi"
            else:
                detail["status"] = "Tidak ada baris Jumlah/Total, dilewati"

            summary["detail_tabel"].append(detail)

    if status_text is not None:
        status_text.write("Selesai memproses semua tabel.")

    return summary


# =========================================================
# GROUP TOTAL PROCESS
# =========================================================

def verify_total_rows_by_group(table, numeric_cols):
    """
    Memproses tabel gabungan yang punya lebih dari satu baris Jumlah/Total.

    Contoh:
    PT AJA
    data...
    Jumlah

    CV DNM
    data...
    Jumlah
    """

    result_total = {
        "total_rows": 0,
        "verified": 0,
        "different": 0
    }

    group_start_idx = 0
    last_after_total_idx = 0

    for row_idx, row in enumerate(table.rows):
        if is_header_number_row(row):
            continue

        if is_group_header_row(row, numeric_cols):
            group_start_idx = row_idx + 1
            continue

        if is_total_row(row):
            if group_start_idx is not None:
                start_idx = group_start_idx
            else:
                start_idx = last_after_total_idx

            vertical_sums = calculate_sums_between_rows(
                table=table,
                start_row_idx=start_idx,
                end_row_idx=row_idx,
                numeric_cols=numeric_cols
            )

            result = verify_total_row(
                total_row=row,
                numeric_cols=numeric_cols,
                vertical_sums=vertical_sums
            )

            result_total["total_rows"] += 1
            result_total["verified"] += result["verified"]
            result_total["different"] += result["different"]

            last_after_total_idx = row_idx + 1
            group_start_idx = None

    return result_total


def is_group_header_row(row, numeric_cols):
    """
    Mendeteksi baris pemisah kelompok/vendor/unit.

    Contoh:
    - PT AJA
    - CV DNM
    - UD MAKMUR
    - TOKO ABC
    """

    if is_total_row(row):
        return False

    if is_header_number_row(row):
        return False

    if row_has_number(row):
        return False

    texts = []

    for cell in row.cells:
        text = cell.text.strip()
        if text:
            texts.append(normalize_text_keep_space(text))

    if not texts:
        return False

    combined_text = " ".join(texts).strip()
    combined_no_space = normalize_text(combined_text)

    if not combined_text:
        return False

    # Jangan sampai header tabel dianggap group header.
    header_words = [
        "NO",
        "SATUAN",
        "PENDIDIKAN",
        "NOMOR",
        "PESANAN",
        "PAKET",
        "PEKERJAAN",
        "NILAI",
        "HASIL",
        "KONFIRMASI",
        "SELISIH",
        "URAIAN",
        "KETERANGAN"
    ]

    header_hit = sum(1 for word in header_words if word in combined_no_space)

    if header_hit >= 2:
        return False

    group_prefixes = [
        "PT ",
        "CV ",
        "UD ",
        "PD ",
        "TOKO ",
        "KOPERASI ",
        "YAYASAN ",
        "DINAS ",
        "BADAN ",
        "BIRO ",
        "SEKRETARIAT ",
        "SEKOLAH ",
        "SMAN ",
        "SMKN ",
        "SMPN ",
        "SDN "
    ]

    for prefix in group_prefixes:
        if combined_text.startswith(prefix):
            return True

    # Fallback:
    # baris teks pendek tanpa angka sering merupakan nama kelompok.
    if len(combined_text.split()) <= 8:
        return True

    return False


# =========================================================
# SUM AND VERIFY
# =========================================================

def calculate_sums_between_rows(table, start_row_idx, end_row_idx, numeric_cols):
    """
    Menjumlahkan angka dari start_row_idx sampai sebelum end_row_idx.
    Fungsi ini sengaja dibuat ringan.
    Tidak memakai deteksi subtotal otomatis yang berat.
    """

    vertical_sums = [0.0] * len(table.columns)

    for row_idx in range(start_row_idx, end_row_idx):
        row = table.rows[row_idx]

        skip, _ = should_skip_row_automatically(
            row=row,
            numeric_cols=numeric_cols
        )

        if skip:
            continue

        for col_idx in numeric_cols:
            if col_idx >= len(row.cells):
                continue

            number = parse_number(row.cells[col_idx].text, dash_as_zero=True)

            if number is None:
                continue

            vertical_sums[col_idx] += number

    return vertical_sums


def verify_total_row(total_row, numeric_cols, vertical_sums):
    result = {
        "verified": 0,
        "different": 0
    }

    for col_idx in numeric_cols:
        if col_idx >= len(total_row.cells):
            continue

        cell = total_row.cells[col_idx]
        existing_number = parse_number(cell.text, dash_as_zero=True)

        if existing_number is None:
            continue

        calculated_number = vertical_sums[col_idx]
        tolerance = max(5, abs(existing_number) * 0.00001)

        if numbers_are_equal(existing_number, calculated_number, tolerance):
            add_status_mark(cell, "^", RGBColor(0, 176, 80))
            add_recalculation_note_to_cell(
                cell=cell,
                calculated_number=calculated_number,
                color=RGBColor(0, 176, 80)
            )
            result["verified"] += 1
        else:
            add_status_mark(cell, "X", RGBColor(255, 0, 0))
            add_recalculation_note_to_cell(
                cell=cell,
                calculated_number=calculated_number,
                color=RGBColor(255, 0, 0)
            )
            result["different"] += 1

    return result


def should_skip_row_automatically(row, numeric_cols):
    """
    Versi ringan.
    Tidak ada deteksi subtotal otomatis yang kompleks.
    """

    if is_header_number_row(row):
        return True, "header_number"

    if is_total_row(row):
        return True, "total"

    if is_group_header_row(row, numeric_cols):
        return True, "group_header"

    if is_likely_header_text_row(row) and not row_has_number(row):
        return True, "header_text"

    return False, ""


# =========================================================
# TOTAL ROW DETECTION
# =========================================================

def find_total_row_indices(table):
    total_indices = []

    for idx, row in enumerate(table.rows):
        if is_total_row(row):
            total_indices.append(idx)

    return total_indices


def is_total_row(row):
    """
    Deteksi baris Jumlah/Total.

    Aman untuk:
    - Jumlah
    - JUMLAH
    - jumlah
    - Total
    - TOTAL
    - total
    - Grand Total

    Tidak menganggap header seperti "Jumlah Temuan" sebagai total.
    """

    if not row_has_number(row):
        return False

    total_words_exact = {
        "JUMLAH",
        "TOTAL",
        "GRANDTOTAL",
        "GRAND TOTAL",
        "JUMLAHSELURUHNYA",
        "JUMLAH SELURUHNYA",
        "TOTALKESELURUHAN",
        "TOTAL KESELURUHAN"
    }

    header_like_words = [
        "TEMUAN",
        "REKOMENDASI",
        "ANGGARAN",
        "REALISASI",
        "TAHUN",
        "LHP",
        "SESUAI",
        "BELUM",
        "TINDAKLANJUT",
        "DITINDAKLANJUTI",
        "NOMOR",
        "NO",
        "PESANAN",
        "PAKET",
        "PEKERJAAN",
        "NILAI",
        "HASIL",
        "KONFIRMASI",
        "SELISIH"
    ]

    texts = []

    for cell in row.cells:
        raw = cell.text.strip()
        if not raw:
            continue

        # Kalau cell berisi angka saja, jangan masuk kandidat label.
        if parse_number(raw, dash_as_zero=False) is not None:
            continue

        no_space = normalize_text(raw)
        with_space = normalize_text_keep_space(raw)

        if no_space:
            texts.append((no_space, with_space))

    if not texts:
        return False

    for no_space, with_space in texts:
        if no_space in total_words_exact or with_space in total_words_exact:
            return True

        if no_space.startswith("JUMLAH") or no_space.startswith("TOTAL") or no_space.startswith("GRANDTOTAL"):
            if any(word in no_space for word in header_like_words):
                continue
            return True

    return False


# =========================================================
# NUMERIC COLUMN DETECTION
# =========================================================

def detect_numeric_columns_for_footing(table):
    numeric_cols = []

    for col_idx in range(len(table.columns)):
        if is_no_column(table, col_idx):
            continue

        if is_percent_column(table, col_idx):
            continue

        numeric_count = 0

        for row in table.rows:
            if is_header_number_row(row):
                continue

            if is_total_row(row):
                continue

            if is_likely_header_text_row(row) and not row_has_number(row):
                continue

            if col_idx >= len(row.cells):
                continue

            number = parse_number(row.cells[col_idx].text, dash_as_zero=True)

            if number is not None:
                numeric_count += 1

            if numeric_count >= 1:
                numeric_cols.append(col_idx)
                break

    return numeric_cols


def is_no_column(table, col_idx):
    """
    Mencegah kolom No ikut dihitung.
    """

    header_text = ""

    for row in table.rows[:5]:
        if col_idx < len(row.cells):
            header_text += " " + normalize_text_keep_space(row.cells[col_idx].text)

    header_text = normalize_text_keep_space(header_text)
    header_no_space = normalize_text(header_text)

    if header_no_space in ["NO", "NOMOR"]:
        return True

    if header_text.startswith("NO "):
        return True

    return False


def is_percent_column(table, col_idx):
    """
    Deteksi kolom persen hanya berdasarkan header.
    Angka kecil tidak otomatis dianggap persen.
    """

    header_text = ""

    for row in table.rows[:8]:
        if col_idx < len(row.cells):
            header_text += " " + normalize_text_keep_space(row.cells[col_idx].text)

    header_no_space = normalize_text(header_text)
    header_with_space = normalize_text_keep_space(header_text)

    percent_keywords = [
        "%",
        "PERSEN",
        "PERSENTASE",
        "PROSENTASE",
        "PRESENTASE",
        "RASIO"
    ]

    for keyword in percent_keywords:
        if keyword in header_no_space or keyword in header_with_space:
            return True

    return False


# =========================================================
# ROW DETECTION
# =========================================================

def is_header_number_row(row):
    """
    Deteksi baris nomor header seperti:
    | 1 | 2 | 3 | 4 |

    Jangan sampai baris data seperti:
    | 2 | Pengadaan dan Instalasi ... | 2.079.833.450,00 |
    dianggap header.
    """

    values = []
    text_like_count = 0
    numeric_like_count = 0

    for cell in row.cells:
        text = cell.text.strip()
        text_clean = text.replace(" ", "").replace("\n", "").replace("\r", "")

        if not text_clean:
            continue

        values.append(text_clean)

        if re.search(r"[A-Za-zÀ-ÿ]", text):
            if not re.match(r"^\d+(\s*=\s*[\d\+\-\*/\(\)]+)?$", text_clean):
                text_like_count += 1

        if re.match(r"^\d+(\s*=\s*[\d\+\-\*/\(\)]+)?$", text_clean):
            numeric_like_count += 1

    if not values:
        return False

    if text_like_count >= 1:
        return False

    if numeric_like_count >= max(2, int(len(values) * 0.6)):
        return True

    return False


def is_likely_header_text_row(row):
    non_empty = []

    for cell in row.cells:
        text = cell.text.strip()
        if text:
            non_empty.append(text)

    if not non_empty:
        return True

    numeric_found = 0

    for text in non_empty:
        if parse_number(text, dash_as_zero=False) is not None:
            numeric_found += 1

    return numeric_found == 0


def row_has_number(row):
    for cell in row.cells:
        if parse_number(cell.text, dash_as_zero=False) is not None:
            return True

    return False


# =========================================================
# MARKING
# =========================================================

def clean_table_old_marks(table):
    for row in table.rows:
        for cell in row.cells:
            clean_existing_marks_and_notes(cell)


def clean_existing_marks_and_notes(cell):
    """
    Membersihkan tanda hasil lama tanpa merusak teks asli.
    Tidak menghapus huruf X pada teks seperti WKP IX.
    """

    for paragraph in cell.paragraphs:
        paragraph_text = paragraph.text or ""

        if "Rekalkulasi:" in paragraph_text:
            for run in paragraph.runs:
                run.text = ""
            continue

        for run in paragraph.runs:
            text = run.text

            # Hapus tanda berdiri sendiri di akhir run.
            text = re.sub(r"\s+\^\s*$", "", text)
            text = re.sub(r"\s+X\s*$", "", text)

            if text.strip() in ["^", "X"]:
                text = ""

            run.text = text


def add_status_mark(cell, mark, color):
    paragraph = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
    paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

    run = paragraph.add_run(f" {mark}")
    run.font.name = "Calibri"
    run.font.size = Pt(16)
    run.font.bold = True
    run.font.color.rgb = color


def add_recalculation_note_to_cell(cell, calculated_number, color=None):
    paragraph = cell.add_paragraph()
    paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

    text = f"Rekalkulasi: {format_number(calculated_number)}"

    if color is None:
        color = RGBColor(255, 0, 0)

    run = paragraph.add_run(text)
    run.font.name = "Calibri"
    run.font.size = Pt(8)
    run.font.bold = True
    run.font.color.rgb = color


# =========================================================
# ADD RECALCULATION ROW
# =========================================================

def add_recalculation_row(table, numeric_cols, vertical_sums):
    if not any(abs(vertical_sums[col]) > 0 for col in numeric_cols):
        return False

    new_row = table.add_row()
    new_row.cells[0].text = "Rekalkulasi Sistem"

    for col_idx in range(len(table.columns)):
        if col_idx in numeric_cols and abs(vertical_sums[col_idx]) > 0:
            cell = new_row.cells[col_idx]
            cell.text = format_number(vertical_sums[col_idx])
            set_recalculation_cell_style(cell)

    return True


def set_recalculation_cell_style(cell):
    for paragraph in cell.paragraphs:
        paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

        for run in paragraph.runs:
            run.font.name = "Calibri"
            run.font.size = Pt(11)
            run.font.color.rgb = RGBColor(255, 0, 0)
            run.bold = True


# =========================================================
# NUMBER PARSER AND FORMATTER
# =========================================================

def parse_number(text, dash_as_zero=True):
    if text is None:
        return None

    text = str(text).strip()

    if text == "":
        return None

    # Kalau sudah ada catatan rekalkulasi, ambil bagian angka awalnya saja.
    if "Rekalkulasi:" in text:
        text = text.split("Rekalkulasi:")[0]

    text = text.replace("\n", "")
    text = text.replace("\r", "")
    text = text.replace("\t", "")
    text = text.replace(" ", "")

    text = text.replace("Rp", "")
    text = text.replace("RP", "")
    text = text.replace("rp", "")
    text = text.replace("%", "")

    # Hapus tanda hasil kalau berdiri sendiri.
    text = re.sub(r"\^", "", text)
    text = re.sub(r"X$", "", text)

    if text in ["", "-", "–", "—"]:
        return 0.0 if dash_as_zero else None

    is_negative = False

    if re.match(r"^\(.+\)$", text):
        is_negative = True
        text = text[1:-1]

    # Format Indonesia:
    # 1.234.567,89 -> 1234567.89
    text = text.replace(".", "")
    text = text.replace(",", ".")

    if not re.match(r"^-?\d+(\.\d+)?$", text):
        return None

    try:
        number = float(text)

        if is_negative:
            number = -abs(number)

        return number

    except ValueError:
        return None


def format_number(number):
    if number is None:
        return ""

    return f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def numbers_are_equal(a, b, tolerance=1):
    return abs(a - b) <= tolerance


def normalize_text(text):
    if text is None:
        return ""

    return (
        str(text)
        .replace(" ", "")
        .replace("\n", "")
        .replace("\r", "")
        .replace("\t", "")
        .strip()
        .upper()
    )


def normalize_text_keep_space(text):
    if text is None:
        return ""

    text = str(text)
    text = text.replace("\n", " ")
    text = text.replace("\r", " ")
    text = text.replace("\t", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip().upper()


# =========================================================
# RUN APP
# =========================================================

if __name__ == "__main__":
    app()

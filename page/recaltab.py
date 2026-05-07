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
        page_title="Rekalkulasi Tabel Word",
        page_icon="📄",
        layout="wide"
    )

    st.title("📄 Rekalkulasi dan Verifikasi Tabel Word")

    st.write(
        """
        Upload dokumen Word `.docx`. Aplikasi akan membaca tabel, melakukan rekalkulasi angka,
        mengecek baris total/jumlah, serta mengecek kolom persentase jika rumusnya bisa disimpulkan otomatis.
        """
    )

    st.info(
        """
        Tanda hasil pemeriksaan:
        - `^` warna hijau = hasil sesuai / verified.
        - `X` warna merah = hasil berbeda dengan hitungan sistem.
        """
    )

    metode = st.radio(
        "Pilih metode rekalkulasi footing",
        [
            "Lewati subtotal otomatis",
            "Hitung semua baris numerik",
            "Hitung hanya baris rincian/leaf rows"
        ],
        index=0
    )

    col1, col2 = st.columns(2)

    with col1:
        tambah_baris_rekalkulasi = st.checkbox(
            "Tambahkan baris Rekalkulasi Sistem jika tabel tidak memiliki baris JUMLAH/TOTAL",
            value=True
        )

    with col2:
        cek_persentase = st.checkbox(
            "Cek kolom persentase/rasio secara otomatis",
            value=True
        )

    tampilkan_debug = st.checkbox(
        "Tampilkan ringkasan proses",
        value=False
    )

    uploaded_file = st.file_uploader(
        "Upload File Word (.docx)",
        type=["docx"]
    )

    if uploaded_file is not None:
        try:
            doc = Document(uploaded_file)

            with st.spinner("Memproses dokumen..."):
                summary = recalculate_tables(
                    doc=doc,
                    metode=metode,
                    tambah_baris_rekalkulasi=tambah_baris_rekalkulasi,
                    cek_persentase=cek_persentase
                )

                output = io.BytesIO()
                doc.save(output)
                output.seek(0)

            st.success("Rekalkulasi selesai!")

            if tampilkan_debug:
                st.subheader("Ringkasan Proses")
                st.json(summary)

            st.download_button(
                label="📥 Unduh Hasil Rekalkulasi",
                data=output,
                file_name="hasil_rekalkulasi.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

        except Exception as e:
            st.error(f"Terjadi kesalahan: {str(e)}")
            st.error("Pastikan file yang diupload adalah dokumen Word `.docx` yang valid.")


# =========================================================
# MAIN PROCESS
# =========================================================

def recalculate_tables(doc, metode, tambah_baris_rekalkulasi=True, cek_persentase=True):
    summary = {
        "jumlah_tabel": len(doc.tables),
        "tabel_diproses": 0,
        "tabel_tanpa_kolom_numerik": 0,
        "baris_total_ditemukan": 0,
        "sel_footing_verified": 0,
        "sel_footing_berbeda": 0,
        "baris_rekalkulasi_ditambahkan": 0,
        "kolom_persen_dicek": 0,
        "sel_persen_verified": 0,
        "sel_persen_berbeda": 0,
        "formula_persen_ditemukan": []
    }

    for table_idx, table in enumerate(doc.tables, start=1):
        if not table.rows:
            continue

        numeric_cols = detect_numeric_columns_for_footing(table)

        if not numeric_cols:
            summary["tabel_tanpa_kolom_numerik"] += 1

            if cek_persentase:
                verify_percentage_columns(
                    table=table,
                    summary=summary,
                    table_idx=table_idx
                )

            continue

        summary["tabel_diproses"] += 1

        vertical_sums = [0.0] * len(table.columns)
        total_rows = []

        rows = list(table.rows)

        for row_idx, row in enumerate(rows):
            if is_header_number_row(row):
                continue

            if is_total_row(row):
                total_rows.append(row)
                continue

            if should_skip_row_by_method(
                table=table,
                row=row,
                row_idx=row_idx,
                numeric_cols=numeric_cols,
                metode=metode
            ):
                continue

            for col_idx in numeric_cols:
                if col_idx >= len(row.cells):
                    continue

                number = parse_number(row.cells[col_idx].text)

                if number is None:
                    continue

                vertical_sums[col_idx] += number

        if total_rows:
            summary["baris_total_ditemukan"] += len(total_rows)

            for total_row in total_rows:
                result = verify_total_row(
                    total_row=total_row,
                    numeric_cols=numeric_cols,
                    vertical_sums=vertical_sums
                )

                summary["sel_footing_verified"] += result["verified"]
                summary["sel_footing_berbeda"] += result["different"]

        else:
            if tambah_baris_rekalkulasi:
                added = add_recalculation_row(
                    table=table,
                    numeric_cols=numeric_cols,
                    vertical_sums=vertical_sums
                )

                if added:
                    summary["baris_rekalkulasi_ditambahkan"] += 1

        if cek_persentase:
            verify_percentage_columns(
                table=table,
                summary=summary,
                table_idx=table_idx
            )

    return summary


# =========================================================
# FOOTING NUMERIC COLUMN DETECTION
# =========================================================

def detect_numeric_columns_for_footing(table, sample_rows=10):
    """
    Deteksi kolom numerik untuk footing.
    Kolom persen/rasio tidak dimasukkan agar tidak dijumlahkan.
    """

    numeric_cols = []
    data_rows = []

    for row in table.rows:
        if is_header_number_row(row):
            continue

        if is_total_row(row):
            continue

        if is_likely_header_text_row(row):
            continue

        data_rows.append(row)

        if len(data_rows) >= sample_rows:
            break

    for col_idx in range(len(table.columns)):
        if is_ratio_or_percent_column(table, col_idx):
            continue

        numeric_count = 0
        checked_count = 0

        for row in data_rows:
            if col_idx >= len(row.cells):
                continue

            text = row.cells[col_idx].text.strip()

            if text == "":
                continue

            checked_count += 1

            if parse_number(text) is not None:
                numeric_count += 1

        if numeric_count > 0:
            numeric_cols.append(col_idx)

    return numeric_cols


def detect_all_numeric_columns(table):
    """
    Deteksi semua kolom numerik, termasuk kolom persen.
    Dipakai untuk simulasi rumus persentase.
    """

    numeric_cols = []

    for col_idx in range(len(table.columns)):
        numeric_count = 0

        for row in table.rows:
            if is_header_number_row(row):
                continue

            if col_idx >= len(row.cells):
                continue

            text = row.cells[col_idx].text.strip()

            if text == "":
                continue

            if parse_number(text) is not None:
                numeric_count += 1

            if numeric_count >= 2:
                numeric_cols.append(col_idx)
                break

    return numeric_cols


# =========================================================
# ROW DETECTION
# =========================================================

def is_total_row(row):
    """
    Mendeteksi baris total/jumlah.
    """

    total_keywords = [
        "JUMLAH",
        "TOTAL",
        "SUM",
        "GRANDTOTAL",
        "SUBJUMLAH",
        "SUBTOTAL"
    ]

    normalized_cells = [
        normalize_text(cell.text)
        for cell in row.cells
    ]

    for text in normalized_cells:
        for keyword in total_keywords:
            if keyword in text:
                return True

    return False


def is_header_number_row(row):
    """
    Mendeteksi baris header angka seperti:
    1 | 2 | 3 | 4 | 5 | 6 | 7=5/3 | 8 | 9=(2+5)-8
    """

    values = []

    for cell in row.cells:
        text = cell.text.strip()
        text = text.replace(" ", "")
        text = text.replace("\n", "")
        text = text.replace("\r", "")

        if text != "":
            values.append(text)

    if not values:
        return False

    pattern = re.compile(r"^\d+(\s*=\s*[\d\+\-\*/\(\)]+)?$")

    matched = 0

    for value in values:
        if pattern.match(value):
            matched += 1

    return matched >= max(2, int(len(values) * 0.6))


def is_likely_header_text_row(row):
    """
    Mendeteksi baris header teks biasa yang tidak berisi angka.
    """

    texts = [cell.text.strip() for cell in row.cells]
    non_empty = [t for t in texts if t != ""]

    if not non_empty:
        return True

    numeric_found = 0

    for text in non_empty:
        if parse_number(text) is not None:
            numeric_found += 1

    return numeric_found == 0


def is_ratio_or_percent_column(table, col_idx):
    """
    Kolom persen/rasio tidak dijumlahkan pada footing.
    """

    rows_to_check = list(table.rows[:8])

    header_text = ""

    for row in rows_to_check:
        if col_idx >= len(row.cells):
            continue

        raw_text = row.cells[col_idx].text.strip()
        header_text += " " + normalize_text(raw_text)

    if "%" in header_text:
        return True

    if "PERSEN" in header_text or "PERSENTASE" in header_text or "RASIO" in header_text:
        return True

    if re.search(r"\d+=.+", header_text):
        return True

    sample_numbers = []

    for row in table.rows:
        if is_header_number_row(row):
            continue

        if is_total_row(row):
            continue

        if col_idx >= len(row.cells):
            continue

        text = row.cells[col_idx].text.strip()

        if text == "":
            continue

        number = parse_number(text)

        if number is not None:
            sample_numbers.append(number)

        if len(sample_numbers) >= 6:
            break

    if len(sample_numbers) >= 3:
        small_ratio_like = 0

        for number in sample_numbers:
            if -500 <= number <= 500 and abs(number) != 0:
                small_ratio_like += 1

        if small_ratio_like >= 3:
            return True

    return False


# =========================================================
# SUBTOTAL / LEAF ROW LOGIC
# =========================================================

def should_skip_row_by_method(table, row, row_idx, numeric_cols, metode):
    """
    Menentukan apakah baris perlu dilewati berdasarkan metode footing.
    """

    if metode == "Hitung semua baris numerik":
        return False

    if metode == "Lewati subtotal otomatis":
        return is_probable_subtotal_row(
            table=table,
            row=row,
            row_idx=row_idx,
            numeric_cols=numeric_cols
        )

    if metode == "Hitung hanya baris rincian/leaf rows":
        return is_non_leaf_row(
            table=table,
            row=row,
            row_idx=row_idx,
            numeric_cols=numeric_cols
        )

    return False


def is_probable_subtotal_row(table, row, row_idx, numeric_cols):
    """
    Baris dianggap subtotal jika angka pada baris tersebut mendekati jumlah
    beberapa baris setelahnya.
    """

    current_values = get_numeric_values(row, numeric_cols)

    if not current_values:
        return False

    next_rows = list(table.rows)[row_idx + 1:]
    candidate_children = []

    for next_row in next_rows:
        if is_header_number_row(next_row):
            continue

        if is_total_row(next_row):
            break

        next_values = get_numeric_values(next_row, numeric_cols)

        if not next_values:
            continue

        candidate_children.append(next_row)

        if len(candidate_children) >= 10:
            break

    if len(candidate_children) < 2:
        return False

    match_count = 0
    checked_count = 0

    for col_idx in numeric_cols:
        if col_idx >= len(row.cells):
            continue

        current_value = parse_number(row.cells[col_idx].text)

        if current_value is None or abs(current_value) < 1:
            continue

        child_sum = 0.0
        child_count = 0

        for child_row in candidate_children:
            if col_idx >= len(child_row.cells):
                continue

            child_value = parse_number(child_row.cells[col_idx].text)

            if child_value is not None:
                child_sum += child_value
                child_count += 1

        if child_count < 2:
            continue

        checked_count += 1

        tolerance = max(5, abs(current_value) * 0.00001)

        if numbers_are_equal(current_value, child_sum, tolerance=tolerance):
            match_count += 1

    if checked_count == 0:
        return False

    return match_count >= 1


def is_non_leaf_row(table, row, row_idx, numeric_cols):
    """
    Mode leaf rows:
    Baris dilewati jika kemungkinan merupakan induk/subtotal.
    """

    if is_probable_subtotal_row(table, row, row_idx, numeric_cols):
        return True

    if is_bold_row(row):
        next_rows = list(table.rows)[row_idx + 1: row_idx + 6]

        numeric_child_found = 0

        for next_row in next_rows:
            if is_total_row(next_row):
                break

            if is_header_number_row(next_row):
                continue

            values = get_numeric_values(next_row, numeric_cols)

            if values:
                numeric_child_found += 1

        if numeric_child_found >= 1:
            return True

    return False


def get_numeric_values(row, numeric_cols):
    values = {}

    for col_idx in numeric_cols:
        if col_idx >= len(row.cells):
            continue

        number = parse_number(row.cells[col_idx].text)

        if number is not None:
            values[col_idx] = number

    return values


def is_bold_row(row):
    """
    Mengecek apakah mayoritas teks dalam baris menggunakan bold.
    """

    total_runs = 0
    bold_runs = 0

    for cell in row.cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                text = run.text.strip()

                if text == "":
                    continue

                total_runs += 1

                if run.bold:
                    bold_runs += 1

    if total_runs == 0:
        return False

    return bold_runs >= max(1, int(total_runs * 0.5))


# =========================================================
# FOOTING VERIFICATION
# =========================================================

def verify_total_row(total_row, numeric_cols, vertical_sums):
    result = {
        "verified": 0,
        "different": 0
    }

    for col_idx in numeric_cols:
        if col_idx >= len(total_row.cells):
            continue

        cell = total_row.cells[col_idx]
        existing_number = parse_number(cell.text)

        if existing_number is None:
            continue

        calculated_number = vertical_sums[col_idx]
        tolerance = max(5, abs(existing_number) * 0.00001)

        if numbers_are_equal(existing_number, calculated_number, tolerance=tolerance):
            add_status_mark(
                cell=cell,
                mark="^",
                color=RGBColor(0, 176, 80)
            )
            result["verified"] += 1
        else:
            add_status_mark(
                cell=cell,
                mark="X",
                color=RGBColor(255, 0, 0)
            )

            add_recalculation_note_to_cell(
                cell=cell,
                calculated_number=calculated_number
            )

            result["different"] += 1

    return result


# =========================================================
# PERCENTAGE FORMULA DETECTION AND VERIFICATION
# =========================================================

def verify_percentage_columns(table, summary=None, table_idx=None):
    """
    Mendeteksi dan memverifikasi kolom persentase.
    Sistem mencoba menyimpulkan rumus dari beberapa sampel baris.
    """

    percent_cols = detect_percentage_columns(table)
    numeric_cols = detect_all_numeric_columns(table)

    results = []

    for percent_col in percent_cols:
        formula = infer_percentage_formula(
            table=table,
            percent_col=percent_col,
            numeric_cols=numeric_cols
        )

        if formula is None:
            continue

        result = apply_percentage_formula_check(
            table=table,
            percent_col=percent_col,
            formula=formula
        )

        results.append(result)

        if summary is not None:
            summary["kolom_persen_dicek"] += 1
            summary["sel_persen_verified"] += result["verified"]
            summary["sel_persen_berbeda"] += result["different"]
            summary["formula_persen_ditemukan"].append({
                "tabel": table_idx,
                "kolom_persen": percent_col + 1,
                "formula": formula["description"],
                "verified": result["verified"],
                "different": result["different"]
            })

    return results


def detect_percentage_columns(table):
    """
    Deteksi kolom persentase berdasarkan header, tanda %, atau pola angka kecil.
    """

    percent_cols = []

    for col_idx in range(len(table.columns)):
        header_text = ""

        for row in table.rows[:8]:
            if col_idx < len(row.cells):
                header_text += " " + normalize_text(row.cells[col_idx].text)

        if "%" in header_text:
            percent_cols.append(col_idx)
            continue

        if "PERSEN" in header_text or "PERSENTASE" in header_text or "RASIO" in header_text:
            percent_cols.append(col_idx)
            continue

        sample_values = []

        for row in table.rows:
            if is_header_number_row(row):
                continue

            if col_idx >= len(row.cells):
                continue

            text = row.cells[col_idx].text.strip()

            if text == "":
                continue

            number = parse_number(text)

            if number is not None:
                sample_values.append(number)

            if len(sample_values) >= 6:
                break

        if len(sample_values) >= 3:
            ratio_like_count = 0

            for value in sample_values:
                if -500 <= value <= 500:
                    ratio_like_count += 1

            if ratio_like_count >= 3:
                percent_cols.append(col_idx)

    return sorted(list(set(percent_cols)))


def infer_percentage_formula(table, percent_col, numeric_cols, min_match=2):
    """
    Menebak rumus kolom persentase.
    Minimal cocok 2 sampel agar rumus dianggap valid.
    """

    candidate_formulas = build_candidate_percentage_formulas(
        percent_col=percent_col,
        numeric_cols=numeric_cols
    )

    best_formula = None
    best_score = 0
    best_tested = 0

    for formula in candidate_formulas:
        match_count = 0
        tested_count = 0

        for row in table.rows:
            if is_header_number_row(row):
                continue

            if is_likely_header_text_row(row):
                continue

            expected = get_cell_number(row, percent_col)

            if expected is None:
                continue

            calculated = calculate_formula_value(row, formula)

            if calculated is None:
                continue

            tested_count += 1

            if percentage_numbers_equal(expected, calculated):
                match_count += 1

            if tested_count >= 10:
                break

        if match_count > best_score:
            best_score = match_count
            best_tested = tested_count
            best_formula = formula

    if best_formula is None:
        return None

    if best_score >= min_match:
        return best_formula

    if best_tested > 0 and best_score / best_tested >= 0.75 and best_score >= 1:
        return best_formula

    return None


def build_candidate_percentage_formulas(percent_col, numeric_cols):
    """
    Membuat kandidat rumus:
    1. ratio: A / B x 100
    2. growth: (A - B) / B x 100
    """

    candidates = []

    value_cols = [col for col in numeric_cols if col != percent_col]

    for numerator_col in value_cols:
        for denominator_col in value_cols:
            if numerator_col == denominator_col:
                continue

            candidates.append({
                "type": "ratio",
                "numerator_col": numerator_col,
                "denominator_col": denominator_col,
                "description": f"Kolom {numerator_col + 1} / Kolom {denominator_col + 1} x 100"
            })

            candidates.append({
                "type": "growth",
                "current_col": numerator_col,
                "previous_col": denominator_col,
                "description": f"(Kolom {numerator_col + 1} - Kolom {denominator_col + 1}) / Kolom {denominator_col + 1} x 100"
            })

    def candidate_priority(formula):
        if formula["type"] == "ratio":
            return (
                abs(percent_col - formula["numerator_col"])
                + abs(percent_col - formula["denominator_col"])
            )

        return (
            abs(percent_col - formula["current_col"])
            + abs(percent_col - formula["previous_col"])
        )

    candidates.sort(key=candidate_priority)

    return candidates


def calculate_formula_value(row, formula):
    """
    Menghitung nilai berdasarkan formula kandidat.
    """

    if formula["type"] == "ratio":
        numerator = get_cell_number(row, formula["numerator_col"])
        denominator = get_cell_number(row, formula["denominator_col"])

        if numerator is None or denominator is None or denominator == 0:
            return None

        return numerator / denominator * 100

    if formula["type"] == "growth":
        current = get_cell_number(row, formula["current_col"])
        previous = get_cell_number(row, formula["previous_col"])

        if current is None or previous is None or previous == 0:
            return None

        return (current - previous) / previous * 100

    return None


def apply_percentage_formula_check(table, percent_col, formula):
    """
    Setelah rumus ditemukan, cek seluruh baris pada kolom persentase.
    """

    result = {
        "percent_col": percent_col,
        "formula": formula["description"],
        "verified": 0,
        "different": 0
    }

    for row in table.rows:
        if is_header_number_row(row):
            continue

        if is_likely_header_text_row(row):
            continue

        if percent_col >= len(row.cells):
            continue

        existing_value = get_cell_number(row, percent_col)

        if existing_value is None:
            continue

        calculated_value = calculate_formula_value(row, formula)

        if calculated_value is None:
            continue

        cell = row.cells[percent_col]

        if percentage_numbers_equal(existing_value, calculated_value):
            add_status_mark(
                cell=cell,
                mark="^",
                color=RGBColor(0, 176, 80)
            )

            result["verified"] += 1

        else:
            add_status_mark(
                cell=cell,
                mark="X",
                color=RGBColor(255, 0, 0)
            )

            add_recalculation_note_to_cell(
                cell=cell,
                calculated_number=calculated_value
            )

            result["different"] += 1

    return result


def get_cell_number(row, col_idx):
    if col_idx >= len(row.cells):
        return None

    return parse_number(row.cells[col_idx].text)


def percentage_numbers_equal(a, b, tolerance=0.05):
    """
    Toleransi untuk persentase.
    87,89 dianggap sesuai dengan 87,894.
    """

    return abs(a - b) <= tolerance


# =========================================================
# MARKING AND NOTES
# =========================================================

def add_status_mark(cell, mark, color):
    """
    Menambahkan tanda:
    ^ hijau = sesuai
    X merah = berbeda
    """

    clean_existing_marks_and_notes(cell)

    paragraph = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
    paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

    run = paragraph.add_run(f" {mark}")
    run.font.name = "Calibri"
    run.font.size = Pt(16)
    run.font.bold = True
    run.font.color.rgb = color


def clean_existing_marks_and_notes(cell):
    """
    Membersihkan tanda lama jika dokumen diproses ulang.
    """

    for paragraph in cell.paragraphs:
        for run in paragraph.runs:
            text = run.text

            text = text.replace(" ^", "")
            text = text.replace(" X", "")
            text = text.replace("^", "")
            text = text.replace("X", "")

            text = re.sub(
                r"\s*Rekalkulasi:\s*[-\d\.\,]+",
                "",
                text
            )

            run.text = text


def add_recalculation_note_to_cell(cell, calculated_number):
    """
    Menambahkan catatan kecil hasil rekalkulasi pada sel yang berbeda.
    """

    paragraph = cell.add_paragraph()
    paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

    run = paragraph.add_run(f"Rekalkulasi: {format_number(calculated_number)}")
    run.font.name = "Calibri"
    run.font.size = Pt(8)
    run.font.bold = True
    run.font.color.rgb = RGBColor(255, 0, 0)


# =========================================================
# ADD RECALCULATION ROW
# =========================================================

def add_recalculation_row(table, numeric_cols, vertical_sums):
    if not any(abs(vertical_sums[col]) > 0 for col in numeric_cols):
        return False

    new_row = table.add_row()
    new_row.cells[0].text = "Rekalkulasi Sistem"

    for col_idx in range(len(table.columns)):
        cell = new_row.cells[col_idx]

        if col_idx in numeric_cols and abs(vertical_sums[col_idx]) > 0:
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

def parse_number(text):
    """
    Mengubah teks angka Indonesia menjadi float.

    Contoh dikenali:
    - 1.105.550.130
    - 99,73
    - 99,73%
    - (17,85)
    - Rp1.000.000,00
    - -
    """

    if text is None:
        return None

    text = str(text).strip()

    if text == "":
        return None

    text = text.replace("\n", "")
    text = text.replace("\r", "")
    text = text.replace("\t", "")
    text = text.replace(" ", "")

    text = text.replace("Rp", "")
    text = text.replace("RP", "")
    text = text.replace("rp", "")

    text = text.replace("%", "")
    text = text.replace("^", "")
    text = text.replace("X", "")

    text = re.sub(
        r"Rekalkulasi:[-\d\.\,]+",
        "",
        text
    )

    if text in ["-", "–", "—"]:
        return 0.0

    is_negative = False

    if re.match(r"^\(.+\)$", text):
        is_negative = True
        text = text[1:-1]

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
    """
    Format angka ke format Indonesia.
    """

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


# =========================================================
# RUN APP
# =========================================================

if __name__ == "__main__":
    app()

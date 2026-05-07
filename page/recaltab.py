import streamlit as st
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import re
import io


# =========================================================
# APP
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
        Upload dokumen Word `.docx`. Aplikasi akan memeriksa:
        - footing baris JUMLAH/TOTAL;
        - kolom persentase;
        - kolom persentase naik/turun.
        """
    )

    st.info(
        """
        Tanda hasil:
        - `^` hijau = sesuai / verified.
        - `X` merah = berbeda dengan hitungan sistem.
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
            "Tambahkan baris Rekalkulasi Sistem jika tidak ada baris JUMLAH/TOTAL",
            value=True
        )

    with col2:
        cek_persentase = st.checkbox(
            "Cek kolom persentase otomatis",
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
            st.error("Pastikan file yang diupload adalah dokumen Word `.docx` valid.")


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

        clean_table_old_marks(table)

        numeric_cols = detect_numeric_columns_for_footing(table)

        total_rows = find_total_rows(table)

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

        rows = list(table.rows)

        for row_idx, row in enumerate(rows):
            if is_header_number_row(row):
                continue

            if row in total_rows:
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

                number = parse_number(row.cells[col_idx].text, dash_as_zero=True)

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
# CLEAN OLD MARKS
# =========================================================

def clean_table_old_marks(table):
    for row in table.rows:
        for cell in row.cells:
            clean_existing_marks_and_notes(cell)


# =========================================================
# TOTAL ROW DETECTION
# =========================================================

def find_total_rows(table):
    total_rows = []

    for row in table.rows:
        if is_total_row(row):
            total_rows.append(row)

    return total_rows


def is_total_row(row):
    """
    Deteksi baris total lebih kuat.
    Fokus utama pada cell pertama/uraian.
    """

    keywords = [
        "JUMLAH",
        "TOTAL",
        "GRANDTOTAL",
        "GRAND TOTAL"
    ]

    cell_texts = [normalize_text(cell.text) for cell in row.cells]

    non_empty = [text for text in cell_texts if text != ""]

    if not non_empty:
        return False

    first_text = non_empty[0]

    for keyword in keywords:
        key = normalize_text(keyword)

        if first_text == key:
            return True

        if first_text.startswith(key):
            return True

        if key in first_text and len(first_text) <= len(key) + 10:
            return True

    for text in non_empty:
        for keyword in keywords:
            key = normalize_text(keyword)

            if text == key:
                return True

    return False


# =========================================================
# NUMERIC COLUMN DETECTION FOR FOOTING
# =========================================================

def detect_numeric_columns_for_footing(table, sample_rows=12):
    """
    Deteksi kolom numerik untuk footing.
    Kolom persentase tidak dihitung sebagai footing.
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
        if is_percent_column(table, col_idx):
            continue

        numeric_count = 0

        for row in data_rows:
            if col_idx >= len(row.cells):
                continue

            text = row.cells[col_idx].text.strip()

            if text == "":
                continue

            number = parse_number(text, dash_as_zero=True)

            if number is not None:
                numeric_count += 1

        if numeric_count >= 1:
            numeric_cols.append(col_idx)

    return numeric_cols


def detect_all_money_value_columns(table):
    """
    Deteksi kolom angka nilai, bukan kolom persentase.
    Dipakai untuk mencari pasangan rumus persentase.
    """

    cols = []

    for col_idx in range(len(table.columns)):
        if is_percent_column(table, col_idx):
            continue

        count = 0

        for row in table.rows:
            if is_header_number_row(row):
                continue

            if col_idx >= len(row.cells):
                continue

            text = row.cells[col_idx].text.strip()

            if text == "":
                continue

            number = parse_number(text, dash_as_zero=True)

            if number is not None:
                count += 1

            if count >= 2:
                cols.append(col_idx)
                break

    return cols


# =========================================================
# ROW / COLUMN DETECTION
# =========================================================

def is_header_number_row(row):
    """
    Deteksi baris header angka:
    1 | 2 | 3 | 4 | 5 | 6 | 7=5/3 | 8 | 9=(2+5)-8
    """

    values = []

    for cell in row.cells:
        text = cell.text.strip()
        text = text.replace(" ", "")
        text = text.replace("\n", "")
        text = text.replace("\r", "")

        if text:
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
    Deteksi baris header teks yang tidak berisi angka.
    """

    texts = [cell.text.strip() for cell in row.cells]
    non_empty = [t for t in texts if t]

    if not non_empty:
        return True

    numeric_found = 0

    for text in non_empty:
        if parse_number(text, dash_as_zero=False) is not None:
            numeric_found += 1

    return numeric_found == 0


def is_percent_column(table, col_idx):
    """
    Deteksi kolom persentase.
    """

    header_text = ""

    for row in table.rows[:8]:
        if col_idx < len(row.cells):
            header_text += " " + normalize_text(row.cells[col_idx].text)

    if "%" in header_text:
        return True

    if "PERSEN" in header_text:
        return True

    if "PERSENTASE" in header_text:
        return True

    if "RASIO" in header_text:
        return True

    if "NAIK" in header_text and "TURUN" in header_text:
        return True

    # Deteksi dari pola isi: banyak angka kecil/desimal seperti 87,89 atau (20,98)
    sample_values = []

    for row in table.rows:
        if is_header_number_row(row):
            continue

        if col_idx >= len(row.cells):
            continue

        raw = row.cells[col_idx].text.strip()

        if raw in ["", "-", "–", "—"]:
            continue

        number = parse_number(raw, dash_as_zero=False)

        if number is not None:
            sample_values.append(number)

        if len(sample_values) >= 6:
            break

    if len(sample_values) >= 3:
        small_count = 0

        for value in sample_values:
            if -500 <= value <= 10000:
                small_count += 1

        if small_count >= 3:
            return True

    return False


def detect_percentage_columns(table):
    percent_cols = []

    for col_idx in range(len(table.columns)):
        if is_percent_column(table, col_idx):
            percent_cols.append(col_idx)

    return sorted(list(set(percent_cols)))


# =========================================================
# SUBTOTAL / LEAF ROW LOGIC
# =========================================================

def should_skip_row_by_method(table, row, row_idx, numeric_cols, metode):
    if metode == "Hitung semua baris numerik":
        return False

    if metode == "Lewati subtotal otomatis":
        return is_probable_subtotal_row(table, row, row_idx, numeric_cols)

    if metode == "Hitung hanya baris rincian/leaf rows":
        return is_non_leaf_row(table, row, row_idx, numeric_cols)

    return False


def is_probable_subtotal_row(table, row, row_idx, numeric_cols):
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

    checked = 0
    matched = 0

    for col_idx in numeric_cols:
        if col_idx >= len(row.cells):
            continue

        current_value = parse_number(row.cells[col_idx].text, dash_as_zero=True)

        if current_value is None or abs(current_value) < 1:
            continue

        child_sum = 0
        child_count = 0

        for child_row in candidate_children:
            if col_idx >= len(child_row.cells):
                continue

            child_value = parse_number(child_row.cells[col_idx].text, dash_as_zero=True)

            if child_value is not None:
                child_sum += child_value
                child_count += 1

        if child_count < 2:
            continue

        checked += 1
        tolerance = max(5, abs(current_value) * 0.00001)

        if numbers_are_equal(current_value, child_sum, tolerance):
            matched += 1

    if checked == 0:
        return False

    return matched >= 1


def is_non_leaf_row(table, row, row_idx, numeric_cols):
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

        number = parse_number(row.cells[col_idx].text, dash_as_zero=True)

        if number is not None:
            values[col_idx] = number

    return values


def is_bold_row(row):
    total_runs = 0
    bold_runs = 0

    for cell in row.cells:
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                if run.text.strip():
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
        existing_number = parse_number(cell.text, dash_as_zero=True)

        if existing_number is None:
            continue

        calculated_number = vertical_sums[col_idx]
        tolerance = max(5, abs(existing_number) * 0.00001)

        if numbers_are_equal(existing_number, calculated_number, tolerance):
            add_status_mark(cell, "^", RGBColor(0, 176, 80))
            result["verified"] += 1
        else:
            add_status_mark(cell, "X", RGBColor(255, 0, 0))
            add_recalculation_note_to_cell(
                cell=cell,
                calculated_number=calculated_number,
                is_percent=False
            )
            result["different"] += 1

    return result


# =========================================================
# PERCENTAGE VERIFICATION
# =========================================================

def verify_percentage_columns(table, summary=None, table_idx=None):
    percent_cols = detect_percentage_columns(table)
    money_cols = detect_all_money_value_columns(table)

    for percent_col in percent_cols:
        formula = infer_percentage_formula(
            table=table,
            percent_col=percent_col,
            money_cols=money_cols
        )

        if formula is None:
            continue

        result = apply_percentage_formula_check(
            table=table,
            percent_col=percent_col,
            formula=formula
        )

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


def infer_percentage_formula(table, percent_col, money_cols, min_match=2):
    candidates = build_candidate_percentage_formulas(
        table=table,
        percent_col=percent_col,
        money_cols=money_cols
    )

    best_formula = None
    best_score = -1
    best_tested = 0

    for formula in candidates:
        tested = 0
        matched = 0

        for row in table.rows:
            if is_header_number_row(row):
                continue

            if is_likely_header_text_row(row):
                continue

            expected = get_cell_number(row, percent_col, dash_as_zero=False)

            if expected is None:
                continue

            calculated = calculate_formula_value(row, formula)

            if calculated is None:
                continue

            tested += 1

            if percentage_numbers_equal(expected, calculated):
                matched += 1

            if tested >= 10:
                break

        if tested == 0:
            continue

        score = matched / tested

        if matched > best_score:
            best_score = matched
            best_tested = tested
            best_formula = formula

    if best_formula is None:
        return None

    if best_score >= min_match:
        return best_formula

    if best_tested > 0 and best_score / max(best_tested, 1) >= 0.70:
        return best_formula

    return None


def build_candidate_percentage_formulas(table, percent_col, money_cols):
    candidates = []

    header_text = get_column_header_text(table, percent_col)

    # Candidate prioritas untuk kolom % biasa:
    # biasanya kolom sebelum % / kolom dua sebelum %
    left_money_cols = [col for col in money_cols if col < percent_col]

    if len(left_money_cols) >= 2:
        numerator = left_money_cols[-1]
        denominator = left_money_cols[-2]

        candidates.append({
            "type": "ratio",
            "numerator_col": numerator,
            "denominator_col": denominator,
            "priority": 0,
            "description": f"Kolom {numerator + 1} / Kolom {denominator + 1} x 100"
        })

    # Candidate prioritas untuk % NAIK/TURUN:
    # cari current value dari kolom sebelum % biasa atau realisasi tahun ini,
    # previous value dari kolom tepat sebelum % naik/turun.
    if "NAIK" in header_text or "TURUN" in header_text:
        previous_candidates = [col for col in money_cols if col < percent_col]

        if previous_candidates:
            previous_col = previous_candidates[-1]

            for current_col in money_cols:
                if current_col == previous_col:
                    continue

                if current_col < previous_col:
                    candidates.append({
                        "type": "growth",
                        "current_col": current_col,
                        "previous_col": previous_col,
                        "priority": 0,
                        "description": f"(Kolom {current_col + 1} - Kolom {previous_col + 1}) / Kolom {previous_col + 1} x 100"
                    })

    # Candidate umum ratio dan growth
    for numerator_col in money_cols:
        for denominator_col in money_cols:
            if numerator_col == denominator_col:
                continue

            candidates.append({
                "type": "ratio",
                "numerator_col": numerator_col,
                "denominator_col": denominator_col,
                "priority": 10 + abs(percent_col - numerator_col) + abs(percent_col - denominator_col),
                "description": f"Kolom {numerator_col + 1} / Kolom {denominator_col + 1} x 100"
            })

            candidates.append({
                "type": "growth",
                "current_col": numerator_col,
                "previous_col": denominator_col,
                "priority": 20 + abs(percent_col - numerator_col) + abs(percent_col - denominator_col),
                "description": f"(Kolom {numerator_col + 1} - Kolom {denominator_col + 1}) / Kolom {denominator_col + 1} x 100"
            })

    candidates.sort(key=lambda x: x["priority"])

    return candidates


def get_column_header_text(table, col_idx):
    text = ""

    for row in table.rows[:8]:
        if col_idx < len(row.cells):
            text += " " + normalize_text(row.cells[col_idx].text)

    return text


def calculate_formula_value(row, formula):
    if formula["type"] == "ratio":
        numerator = get_cell_number(row, formula["numerator_col"], dash_as_zero=True)
        denominator = get_cell_number(row, formula["denominator_col"], dash_as_zero=True)

        if numerator is None or denominator is None or denominator == 0:
            return None

        return numerator / denominator * 100

    if formula["type"] == "growth":
        current = get_cell_number(row, formula["current_col"], dash_as_zero=True)
        previous = get_cell_number(row, formula["previous_col"], dash_as_zero=True)

        if current is None or previous is None or previous == 0:
            return None

        return (current - previous) / previous * 100

    return None


def apply_percentage_formula_check(table, percent_col, formula):
    result = {
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

        existing_value = get_cell_number(row, percent_col, dash_as_zero=False)

        if existing_value is None:
            continue

        calculated_value = calculate_formula_value(row, formula)

        if calculated_value is None:
            continue

        cell = row.cells[percent_col]

        if percentage_numbers_equal(existing_value, calculated_value):
            add_status_mark(cell, "^", RGBColor(0, 176, 80))
            result["verified"] += 1
        else:
            add_status_mark(cell, "X", RGBColor(255, 0, 0))
            add_recalculation_note_to_cell(
                cell=cell,
                calculated_number=calculated_value,
                is_percent=True
            )
            result["different"] += 1

    return result


def get_cell_number(row, col_idx, dash_as_zero=True):
    if col_idx >= len(row.cells):
        return None

    return parse_number(row.cells[col_idx].text, dash_as_zero=dash_as_zero)


def percentage_numbers_equal(a, b, tolerance=0.05):
    return abs(a - b) <= tolerance


# =========================================================
# MARKING
# =========================================================

def add_status_mark(cell, mark, color):
    paragraph = cell.paragraphs[0] if cell.paragraphs else cell.add_paragraph()
    paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

    run = paragraph.add_run(f" {mark}")
    run.font.name = "Calibri"
    run.font.size = Pt(16)
    run.font.bold = True
    run.font.color.rgb = color


def clean_existing_marks_and_notes(cell):
    paragraphs_to_clear = []

    for paragraph in cell.paragraphs:
        full_text = paragraph.text

        if "Rekalkulasi:" in full_text:
            paragraphs_to_clear.append(paragraph)
            continue

        for run in paragraph.runs:
            text = run.text
            text = text.replace(" ^", "")
            text = text.replace(" X", "")
            text = text.replace("^", "")
            text = text.replace("X", "")
            run.text = text

    # Kosongkan paragraf catatan lama
    for paragraph in paragraphs_to_clear:
        for run in paragraph.runs:
            run.text = ""


def add_recalculation_note_to_cell(cell, calculated_number, is_percent=False):
    paragraph = cell.add_paragraph()
    paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT

    if is_percent:
        text = f"Rekalkulasi: {format_percent(calculated_number)}"
    else:
        text = f"Rekalkulasi: {format_number(calculated_number)}"

    run = paragraph.add_run(text)
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
# NUMBER PARSER
# =========================================================

def parse_number(text, dash_as_zero=True):
    """
    Mengubah angka format Indonesia menjadi float.

    dash_as_zero=True:
    - dipakai untuk footing, sehingga '-' dianggap 0.

    dash_as_zero=False:
    - dipakai untuk persentase, sehingga '-' tidak dicek.
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

    text = re.sub(r"Rekalkulasi:[-\d\.\,\(\)]+", "", text)

    if text in ["-", "–", "—"]:
        return 0.0 if dash_as_zero else None

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
    if number is None:
        return ""

    return f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_percent(number):
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
# RUN
# =========================================================

if __name__ == "__main__":
    app()

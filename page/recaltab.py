import streamlit as st
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
import re
import io
from difflib import SequenceMatcher


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

        Versi ini sudah diperbaiki untuk menangani tabel yang terpotong antar halaman,
        header tabel berulang, dan satu tabel logis yang terbaca sebagai beberapa tabel Word.
        """
    )

    st.info(
        """
        Tanda hasil pemeriksaan:
        - `^` hijau = sesuai.
        - `X` merah = berbeda dengan hasil rekalkulasi.
        """
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        tambah_baris_rekalkulasi = st.checkbox(
            "Jika tidak ada baris Jumlah/Total, tambahkan baris Rekalkulasi Sistem",
            value=False
        )

    with col2:
        gabungkan_tabel_lanjutan = st.checkbox(
            "Gabungkan tabel lanjutan antar halaman",
            value=True
        )

    with col3:
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
                    gabungkan_tabel_lanjutan=gabungkan_tabel_lanjutan,
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

def recalculate_tables(
    doc,
    tambah_baris_rekalkulasi=False,
    gabungkan_tabel_lanjutan=True,
    progress=None,
    status_text=None
):
    summary = {
        "jumlah_tabel_fisik_word": len(doc.tables),
        "jumlah_kelompok_tabel_logis": 0,
        "kelompok_diproses": 0,
        "kelompok_tanpa_kolom_numerik": 0,
        "baris_total_biasa_ditemukan": 0,
        "baris_total_per_kelompok_ditemukan": 0,
        "baris_rekalkulasi_ditambahkan": 0,
        "sel_verified": 0,
        "sel_berbeda": 0,
        "detail_kelompok": []
    }

    if not doc.tables:
        return summary

    for table in doc.tables:
        clean_table_old_marks(table)

    if gabungkan_tabel_lanjutan:
        logical_groups = build_logical_table_groups(doc.tables)
    else:
        logical_groups = []
        for idx, table in enumerate(doc.tables):
            logical_groups.append({
                "group_no": idx + 1,
                "tables": [table],
                "table_indices": [idx + 1],
                "reason": "mode tanpa penggabungan tabel lanjutan"
            })

    summary["jumlah_kelompok_tabel_logis"] = len(logical_groups)

    total_groups = len(logical_groups)

    for group_idx, group in enumerate(logical_groups, start=1):
        if progress is not None and total_groups > 0:
            progress.progress(group_idx / total_groups)

        if status_text is not None:
            status_text.write(
                f"Memproses kelompok tabel logis {group_idx} dari {total_groups}..."
            )

        row_refs = collect_row_refs_from_group(group)

        if not row_refs:
            continue

        numeric_cols = detect_numeric_columns_for_logical_group(row_refs)

        detail = {
            "kelompok": group_idx,
            "tabel_fisik_word": group["table_indices"],
            "jumlah_fragment": len(group["tables"]),
            "jumlah_baris_logis": len(row_refs),
            "numeric_cols": [c + 1 for c in numeric_cols],
            "reason": group.get("reason", ""),
            "status": ""
        }

        if not numeric_cols:
            summary["kelompok_tanpa_kolom_numerik"] += 1
            detail["status"] = "Dilewati, tidak ada kolom numerik"
            summary["detail_kelompok"].append(detail)
            continue

        summary["kelompok_diproses"] += 1

        total_row_positions = find_total_row_positions(row_refs)

        if len(total_row_positions) == 0:
            if tambah_baris_rekalkulasi:
                last_table = group["tables"][-1]

                vertical_sums = calculate_sums_between_row_refs(
                    row_refs=row_refs,
                    start_pos=0,
                    end_pos=len(row_refs),
                    numeric_cols=numeric_cols
                )

                added = add_recalculation_row(
                    table=last_table,
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

            summary["detail_kelompok"].append(detail)
            continue

        if len(total_row_positions) == 1:
            total_pos = total_row_positions[0]

            vertical_sums = calculate_sums_between_row_refs(
                row_refs=row_refs,
                start_pos=0,
                end_pos=total_pos,
                numeric_cols=numeric_cols
            )

            result = verify_total_row(
                total_row=row_refs[total_pos]["row"],
                numeric_cols=numeric_cols,
                vertical_sums=vertical_sums
            )

            summary["baris_total_biasa_ditemukan"] += 1
            summary["sel_verified"] += result["verified"]
            summary["sel_berbeda"] += result["different"]

            detail["status"] = "Diproses sebagai satu tabel logis dengan satu baris total"
            detail["baris_total_logis"] = total_pos + 1
            detail["verified"] = result["verified"]
            detail["different"] = result["different"]
            summary["detail_kelompok"].append(detail)
            continue

        if len(total_row_positions) > 1:
            result_group = verify_total_rows_by_logical_group(
                row_refs=row_refs,
                numeric_cols=numeric_cols
            )

            summary["baris_total_per_kelompok_ditemukan"] += result_group["total_rows"]
            summary["sel_verified"] += result_group["verified"]
            summary["sel_berbeda"] += result_group["different"]

            detail["status"] = "Diproses sebagai tabel dengan beberapa baris total/subtotal"
            detail["baris_total_per_kelompok"] = result_group["total_rows"]
            detail["verified"] = result_group["verified"]
            detail["different"] = result_group["different"]
            summary["detail_kelompok"].append(detail)
            continue

    if status_text is not None:
        status_text.write("Selesai memproses semua tabel.")

    return summary


# =========================================================
# LOGICAL TABLE GROUPING
# =========================================================

def build_logical_table_groups(tables):
    """
    Menggabungkan tabel fisik Word yang sebenarnya merupakan satu tabel logis.
    Cocok untuk kasus tabel terpotong antar halaman dan header muncul ulang.
    """

    groups = []
    current_group = None
    previous_info = None

    for idx, table in enumerate(tables):
        info = analyze_table_structure(table, idx + 1)

        if current_group is None:
            current_group = {
                "group_no": len(groups) + 1,
                "tables": [table],
                "table_indices": [idx + 1],
                "infos": [info],
                "reason": "awal kelompok"
            }
            previous_info = info
            continue

        if is_continuation_table(previous_info, info):
            current_group["tables"].append(table)
            current_group["table_indices"].append(idx + 1)
            current_group["infos"].append(info)
            current_group["reason"] = "digabung karena header/struktur tabel mirip atau nomor urut berlanjut"
        else:
            groups.append(current_group)
            current_group = {
                "group_no": len(groups) + 1,
                "tables": [table],
                "table_indices": [idx + 1],
                "infos": [info],
                "reason": "awal kelompok baru"
            }

        previous_info = info

    if current_group is not None:
        groups.append(current_group)

    return groups


def analyze_table_structure(table, table_index):
    row_count = len(table.rows)
    col_count = len(table.columns)

    header_signature = get_table_header_signature(table)
    first_no = get_first_no_value(table)
    last_no = get_last_no_value(table)
    has_total = any(is_total_row(row) for row in table.rows)
    numeric_cols_preview = detect_numeric_columns_for_physical_table(table)

    return {
        "table_index": table_index,
        "row_count": row_count,
        "col_count": col_count,
        "header_signature": header_signature,
        "first_no": first_no,
        "last_no": last_no,
        "has_total": has_total,
        "numeric_cols_preview": numeric_cols_preview
    }


def get_table_header_signature(table):
    """
    Membuat identitas header tabel.
    Mengambil 1-3 baris awal yang kelihatan seperti header.
    """

    header_parts = []

    max_header_rows = min(4, len(table.rows))

    for row_idx in range(max_header_rows):
        row = table.rows[row_idx]

        if is_total_row(row):
            continue

        if is_header_number_row(row):
            continue

        if is_likely_column_header_row(row):
            texts = []
            for cell in row.cells:
                text = normalize_text_keep_space(cell.text)
                if text:
                    texts.append(text)
            if texts:
                header_parts.append(" | ".join(texts))

    if not header_parts and len(table.rows) > 0:
        first_row_texts = []
        for cell in table.rows[0].cells:
            text = normalize_text_keep_space(cell.text)
            if text:
                first_row_texts.append(text)
        header_parts.append(" | ".join(first_row_texts))

    signature = " || ".join(header_parts)
    signature = normalize_header_signature(signature)

    return signature


def normalize_header_signature(text):
    text = normalize_text_keep_space(text)

    text = re.sub(r"\b20\d{2}\b", "TAHUN", text)
    text = re.sub(r"\b19\d{2}\b", "TAHUN", text)
    text = re.sub(r"\d+", "N", text)

    text = text.replace(".", "")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def is_continuation_table(prev_info, curr_info):
    """
    Menentukan apakah tabel saat ini adalah lanjutan dari tabel sebelumnya.
    """

    if prev_info is None or curr_info is None:
        return False

    if prev_info["col_count"] != curr_info["col_count"]:
        return False

    prev_sig = prev_info.get("header_signature", "")
    curr_sig = curr_info.get("header_signature", "")

    header_similarity = similarity_ratio(prev_sig, curr_sig)

    numbering_continues = False
    if prev_info.get("last_no") is not None and curr_info.get("first_no") is not None:
        numbering_continues = curr_info["first_no"] > prev_info["last_no"]

    same_numeric_pattern = (
        prev_info.get("numeric_cols_preview") == curr_info.get("numeric_cols_preview")
        and len(prev_info.get("numeric_cols_preview", [])) > 0
    )

    # Kasus paling kuat: header sama/mirip.
    if header_similarity >= 0.78:
        return True

    # Kasus tabel lanjutan hasil konversi: nomor berlanjut dan pola kolom angka sama.
    if numbering_continues and same_numeric_pattern and header_similarity >= 0.45:
        return True

    # Kasus header fragment pertama kurang lengkap, tetapi nomor urut jelas berlanjut.
    if numbering_continues and same_numeric_pattern:
        if not prev_info.get("has_total", False):
            return True

    return False


def similarity_ratio(a, b):
    if not a or not b:
        return 0.0

    return SequenceMatcher(None, a, b).ratio()


def collect_row_refs_from_group(group):
    row_refs = []

    for table_pos, table in enumerate(group["tables"]):
        table_index = group["table_indices"][table_pos]

        for row_idx, row in enumerate(table.rows):
            row_refs.append({
                "table": table,
                "table_index": table_index,
                "row": row,
                "row_index": row_idx,
                "global_pos": len(row_refs)
            })

    return row_refs


# =========================================================
# GROUP TOTAL PROCESS
# =========================================================

def verify_total_rows_by_logical_group(row_refs, numeric_cols):
    """
    Memproses satu tabel logis yang punya lebih dari satu baris Jumlah/Total.
    Cocok untuk model:
    PT A
    data
    Jumlah

    CV B
    data
    Jumlah
    """

    result_total = {
        "total_rows": 0,
        "verified": 0,
        "different": 0
    }

    group_start_pos = 0
    last_after_total_pos = 0

    for pos, ref in enumerate(row_refs):
        row = ref["row"]

        if is_repeated_header_row(row):
            continue

        if is_group_header_row(row, numeric_cols):
            group_start_pos = pos + 1
            continue

        if is_total_row(row):
            start_pos = group_start_pos if group_start_pos is not None else last_after_total_pos

            vertical_sums = calculate_sums_between_row_refs(
                row_refs=row_refs,
                start_pos=start_pos,
                end_pos=pos,
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

            last_after_total_pos = pos + 1
            group_start_pos = pos + 1

    return result_total


# =========================================================
# SUM AND VERIFY
# =========================================================

def calculate_sums_between_row_refs(row_refs, start_pos, end_pos, numeric_cols):
    max_col = get_max_col_from_row_refs(row_refs)
    vertical_sums = [0.0] * max_col

    for pos in range(start_pos, end_pos):
        if pos < 0 or pos >= len(row_refs):
            continue

        row = row_refs[pos]["row"]

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


def get_max_col_from_row_refs(row_refs):
    max_col = 0

    for ref in row_refs:
        row = ref["row"]
        max_col = max(max_col, len(row.cells))

    return max_col


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
    if is_repeated_header_row(row):
        return True, "repeated_header"

    if is_header_number_row(row):
        return True, "header_number"

    if is_total_row(row):
        return True, "total"

    if is_group_header_row(row, numeric_cols):
        return True, "group_header"

    if is_likely_header_text_row(row):
        return True, "header_text"

    return False, ""


# =========================================================
# TOTAL ROW DETECTION
# =========================================================

def find_total_row_positions(row_refs):
    total_positions = []

    for pos, ref in enumerate(row_refs):
        if is_total_row(ref["row"]):
            total_positions.append(pos)

    return total_positions


def is_total_row(row):
    """
    Deteksi baris Jumlah/Total.

    Tidak terlalu bergantung pada kewajiban ada angka,
    karena kadang hasil konversi membuat angka total tidak terbaca sempurna.
    """

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
        "SELISIH",
        "KOLOM",
        "URAIAN"
    ]

    texts = []

    for cell in row.cells:
        raw = cell.text.strip()
        if not raw:
            continue

        if parse_number(raw, dash_as_zero=False) is not None:
            continue

        no_space = normalize_text(raw)
        with_space = normalize_text_keep_space(raw)

        if no_space:
            texts.append((no_space, with_space))

    if not texts:
        return False

    row_has_any_number = row_has_number(row)

    for no_space, with_space in texts:
        if no_space in total_words_exact or with_space in total_words_exact:
            return True

        if no_space.startswith("JUMLAH") or no_space.startswith("TOTAL") or no_space.startswith("GRANDTOTAL"):
            if any(word in no_space for word in header_like_words):
                continue

            # Supaya kata "Jumlah ..." di header tidak mudah dianggap total.
            if not row_has_any_number and len(no_space) > 25:
                continue

            return True

    return False


# =========================================================
# NUMERIC COLUMN DETECTION
# =========================================================

def detect_numeric_columns_for_logical_group(row_refs):
    if not row_refs:
        return []

    max_col = get_max_col_from_row_refs(row_refs)
    numeric_cols = []

    for col_idx in range(max_col):
        if is_no_column_from_row_refs(row_refs, col_idx):
            continue

        if is_percent_column_from_row_refs(row_refs, col_idx):
            continue

        numeric_count = 0
        data_row_count = 0

        for ref in row_refs:
            row = ref["row"]

            if is_repeated_header_row(row):
                continue

            if is_header_number_row(row):
                continue

            if is_total_row(row):
                continue

            if is_likely_header_text_row(row):
                continue

            if col_idx >= len(row.cells):
                continue

            data_row_count += 1
            number = parse_number(row.cells[col_idx].text, dash_as_zero=True)

            if number is not None:
                numeric_count += 1

        if numeric_count >= 1:
            numeric_cols.append(col_idx)

    return numeric_cols


def detect_numeric_columns_for_physical_table(table):
    row_refs = []

    for row_idx, row in enumerate(table.rows):
        row_refs.append({
            "table": table,
            "table_index": 0,
            "row": row,
            "row_index": row_idx,
            "global_pos": row_idx
        })

    return detect_numeric_columns_for_logical_group(row_refs)


def is_no_column_from_row_refs(row_refs, col_idx):
    header_text = ""

    for ref in row_refs[:8]:
        row = ref["row"]
        if col_idx < len(row.cells):
            header_text += " " + normalize_text_keep_space(row.cells[col_idx].text)

    header_text = normalize_text_keep_space(header_text)
    header_no_space = normalize_text(header_text)

    no_keywords = [
        "NO",
        "NO.",
        "NOMOR"
    ]

    if header_no_space in ["NO", "NOMOR"]:
        return True

    if header_text in no_keywords:
        return True

    if header_text.startswith("NO "):
        return True

    # Fallback: jika mayoritas isi kolom angka kecil berurutan, kemungkinan kolom nomor.
    values = []

    for ref in row_refs:
        row = ref["row"]

        if is_repeated_header_row(row) or is_header_number_row(row) or is_total_row(row):
            continue

        if col_idx >= len(row.cells):
            continue

        val = parse_number(row.cells[col_idx].text, dash_as_zero=False)

        if val is not None:
            values.append(val)

    if len(values) >= 3:
        small_integer_count = 0
        for val in values:
            if abs(val - int(val)) < 0.00001 and 0 <= val <= 500:
                small_integer_count += 1

        if small_integer_count >= max(3, int(len(values) * 0.8)):
            return True

    return False


def is_percent_column_from_row_refs(row_refs, col_idx):
    header_text = ""

    for ref in row_refs[:10]:
        row = ref["row"]
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

def is_repeated_header_row(row):
    if is_header_number_row(row):
        return True

    if is_likely_column_header_row(row):
        return True

    return False


def is_header_number_row(row):
    """
    Deteksi baris nomor header seperti:
    | 1 | 2 | 3 | 4 |
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


def is_likely_column_header_row(row):
    """
    Header kolom seperti:
    No. | Tahun Pajak | Saldo Per 1 Januari 2026 | Ketetapan 2026 | ...
    harus diabaikan walaupun mengandung angka tahun.
    """

    combined = " ".join(
        normalize_text_keep_space(cell.text)
        for cell in row.cells
        if cell.text and cell.text.strip()
    )

    if not combined:
        return False

    combined_no_space = normalize_text(combined)

    header_keywords = [
        "NO",
        "NOMOR",
        "URAIAN",
        "KETERANGAN",
        "TAHUN",
        "PAJAK",
        "SALDO",
        "KETETAPAN",
        "PEMBAYARAN",
        "DESEMBER",
        "JANUARI",
        "NILAI",
        "REALISASI",
        "ANGGARAN",
        "JUMLAH BARANG",
        "JUMLAHBARANG",
        "SATUAN",
        "VOLUME",
        "HARGA",
        "TOTAL"
    ]

    hit = 0
    for keyword in header_keywords:
        if normalize_text(keyword) in combined_no_space:
            hit += 1

    if hit >= 2:
        # Jangan sampai baris total dianggap header.
        if is_total_row_light(row):
            return False
        return True

    return False


def is_total_row_light(row):
    combined = " ".join(
        normalize_text_keep_space(cell.text)
        for cell in row.cells
        if cell.text and cell.text.strip()
    )

    combined_no_space = normalize_text(combined)

    if combined_no_space in ["JUMLAH", "TOTAL", "GRANDTOTAL"]:
        return True

    if combined_no_space.startswith("JUMLAH") and row_has_number(row):
        return True

    if combined_no_space.startswith("TOTAL") and row_has_number(row):
        return True

    return False


def is_likely_header_text_row(row):
    """
    Baris teks murni tanpa angka nominal.
    Header kolom tetap dianggap header walaupun ada angka tahun.
    """

    if is_likely_column_header_row(row):
        return True

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


def is_group_header_row(row, numeric_cols):
    """
    Deteksi baris pemisah kelompok/vendor/unit.

    Dibuat lebih hati-hati dibanding kode lama.
    Tidak semua teks pendek otomatis dianggap group header.
    """

    if is_total_row(row):
        return False

    if is_repeated_header_row(row):
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

    header_words = [
        "NO",
        "TAHUN",
        "PAJAK",
        "SALDO",
        "KETETAPAN",
        "PEMBAYARAN",
        "DESEMBER",
        "JANUARI",
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
        "SDN ",
        "UPT ",
        "RSUD ",
        "PUSKESMAS "
    ]

    for prefix in group_prefixes:
        if combined_text.startswith(prefix):
            return True

    # Fallback aman:
    # hanya dianggap group header bila hanya 1-2 cell terisi,
    # teks cukup pendek, dan bukan header tabel.
    non_empty_cell_count = len(texts)

    if non_empty_cell_count <= 2 and len(combined_text.split()) <= 8:
        return True

    return False


# =========================================================
# NUMBERING DETECTION FOR CONTINUATION
# =========================================================

def get_first_no_value(table):
    for row in table.rows:
        if is_repeated_header_row(row):
            continue

        val = get_no_value_from_row(row)

        if val is not None:
            return val

    return None


def get_last_no_value(table):
    last_val = None

    for row in table.rows:
        if is_repeated_header_row(row):
            continue

        if is_total_row(row):
            continue

        val = get_no_value_from_row(row)

        if val is not None:
            last_val = val

    return last_val


def get_no_value_from_row(row):
    if len(row.cells) == 0:
        return None

    text = row.cells[0].text.strip()

    if not text:
        return None

    text = text.replace(".", "").strip()

    if not re.match(r"^\d+$", text):
        return None

    try:
        return int(text)
    except ValueError:
        return None


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
    if not numeric_cols:
        return False

    if not any(
        col < len(vertical_sums) and abs(vertical_sums[col]) > 0
        for col in numeric_cols
    ):
        return False

    new_row = table.add_row()

    if len(new_row.cells) > 0:
        new_row.cells[0].text = "Rekalkulasi Sistem"

    for col_idx in range(len(table.columns)):
        if col_idx in numeric_cols and col_idx < len(vertical_sums):
            if abs(vertical_sums[col_idx]) > 0:
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

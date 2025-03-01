import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz
import re

# Fungsi untuk membersihkan teks
def preprocess_text(text):
    # 1. Ekspansi singkatan
    text = re.sub(r'\bSDN\b', 'SD NEGERI', text, flags=re.IGNORECASE)
    text = re.sub(r'\bSMPN\b', 'SMP NEGERI', text, flags=re.IGNORECASE)
    text = re.sub(r'\bSMAN\b', 'SMA NEGERI', text, flags=re.IGNORECASE)
    
    # 2. Hapus karakter non-alfanumerik
    text = re.sub(r'[^\w\s]', '', text)
    
    # 3. Hapus informasi alamat (contoh: "Jl. ...")
    text = re.sub(r'\bJl\.?\s+[\w\s]+?(?=\bSD\b|\bSMP\b|\bSMA\b|$)', '', text, flags=re.IGNORECASE)
    
    # 4. Normalisasi case dan spasi
    return " ".join(text.upper().split())

# Fungsi utama fuzzy search
def enhanced_fuzzy_search(data_list, target_text, threshold=70):
    best_match = None
    best_score = 0
    
    # Preprocessing target
    target_clean = preprocess_text(target_text)
    
    for item in data_list:
        if not isinstance(item, str):
            continue
            
        # Preprocessing data
        item_clean = preprocess_text(item)
        
        # Hitung skor dengan kombinasi metrik
        set_ratio = fuzz.token_set_ratio(item_clean, target_clean)
        partial_ratio = fuzz.partial_ratio(item_clean, target_clean)
        combined_score = (2 * set_ratio + partial_ratio) // 3  # Bobot lebih ke token_set
        
        if combined_score >= threshold and combined_score > best_score:
            best_match = item
            best_score = combined_score
            
    return (best_match, best_score) if best_score > 0 else (None, None)

# Antarmuka Streamlit
def app():
    st.title("Fuzzy Search untuk Data Sekolah")
    
    # Session state
    if 'data_list' not in st.session_state:
        st.session_state['data_list'] = []
    if 'target_df' not in st.session_state:
        st.session_state['target_df'] = None

    # Upload Data Sekolah
    st.subheader("1. Upload Data Sekolah (Kolom: Data)")
    data_file = st.file_uploader("Upload file Excel", type=["xlsx"], key="data_uploader")
    if data_file:
        try:
            df = pd.read_excel(data_file)
            st.session_state['data_list'] = df['Data'].dropna().str.strip().tolist()
            st.success(f"✅ {len(st.session_state['data_list'])} data sekolah terdeteksi")
        except Exception as e:
            st.error(f"❌ Gagal membaca data: {e}")

    # Upload Target
    st.subheader("2. Upload Data Target (Kolom: Target)")
    target_file = st.file_uploader("Upload file Excel", type=["xlsx"], key="target_uploader")
    if target_file:
        try:
            df = pd.read_excel(target_file)
            st.session_state['target_df'] = df
            st.success(f"✅ {len(df)} data target terdeteksi")
        except Exception as e:
            st.error(f"❌ Gagal membaca target: {e}")

    # Parameter Pencarian
    st.subheader("3. Parameter Pencarian")
    threshold = st.slider("Threshold Kemiripan", 50, 100, 75, 5)
    st.info(f"Sensitivitas saat ini: {threshold}%")

    # Proses Pencarian
    if st.button("🔍 Mulai Pencarian"):
        if not st.session_state['data_list']:
            st.warning("⚠️ Data sekolah belum diupload")
            return
        if st.session_state['target_df'] is None:
            st.warning("⚠️ Data target belum diupload")
            return
        
        # Proses tiap baris target
        results = []
        for _, row in st.session_state['target_df'].iterrows():
            target_text = row.get('Target', '')
            
            # Skip jika bukan string atau kosong
            if not isinstance(target_text, str) or not target_text.strip():
                results.append((None, None))
                continue
                
            match, score = enhanced_fuzzy_search(
                st.session_state['data_list'],
                target_text,
                threshold
            )
            results.append((match, score))
        
        # Tambahkan hasil ke DataFrame
        result_df = st.session_state['target_df'].copy()
        result_df["Hasil Pencarian"] = [r[0] for r in results]
        result_df["Tingkat Kemiripan"] = [r[1] for r in results]
        
        # Tampilkan hasil
        st.subheader("Hasil Pencarian")
        st.dataframe(result_df.style.applymap(
            lambda x: 'background-color: #d4edda' if isinstance(x, int) and x >= threshold else ''
        ))
        
        # Download hasil
        csv = result_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Hasil (CSV)",
            data=csv,
            file_name="hasil_pencarian.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    app()

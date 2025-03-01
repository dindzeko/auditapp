import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz
import re
from io import BytesIO

# Fungsi pembersihan teks yang diperkuat
def preprocess_text(text):
    # 1. Ekspansi singkatan (case-insensitive)
    text = re.sub(r'\bsdn\b', 'SD NEGERI', text, flags=re.IGNORECASE)
    text = re.sub(r'\bsmpn\b', 'SMP NEGERI', text, flags=re.IGNORECASE)
    text = re.sub(r'\bsman\b', 'SMA NEGERI', text, flags=re.IGNORECASE)
    
    # 2. Hapus semua karakter non-alfanumerik
    text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
    
    # 3. Hapus alamat dan teks sebelum nama sekolah
    text = re.sub(
        r'(.*?)(SD NEGERI|SMP NEGERI|SMA NEGERI|\bSD\b|\bSMP\b|\bSMA\b)', 
        r'\2', 
        text,
        flags=re.IGNORECASE
    )
    
    # 4. Normalisasi case dan hapus spasi berlebih
    text = " ".join(text.upper().split())
    
    # 5. Hapus duplikasi nama sekolah dalam satu teks
    tokens = text.split()
    seen = set()
    deduped = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            deduped.append(token)
    return " ".join(deduped)

# Fungsi fuzzy search yang diperbaiki
def enhanced_fuzzy_search(data_list, target_text, threshold=70):
    best_match = None
    best_score = 0
    
    target_clean = preprocess_text(target_text)
    
    for item in data_list:
        if not isinstance(item, str):
            continue
            
        item_clean = preprocess_text(item)
        
        # Gunakan kombinasi metrik dengan penyesuaian bobot
        set_ratio = fuzz.token_set_ratio(item_clean, target_clean)
        partial_ratio = fuzz.partial_ratio(item_clean, target_clean)
        combined_score = (3 * set_ratio + 2 * partial_ratio) // 5  # Bobot 60% token_set
        
        if combined_score > best_score and combined_score >= threshold:
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
        
        results = []
        for _, row in st.session_state['target_df'].iterrows():
            target_text = row.get('Target', '')
            
            if not isinstance(target_text, str) or not target_text.strip():
                results.append((None, None))
                continue
                
            match, score = enhanced_fuzzy_search(
                st.session_state['data_list'],
                target_text,
                threshold
            )
            results.append((match, score))
        
        # Tampilkan hasil
        result_df = st.session_state['target_df'].copy()
        result_df["Hasil Pencarian"] = [r[0] for r in results]
        result_df["Tingkat Kemiripan"] = [r[1] for r in results]
        
        st.subheader("Hasil Pencarian")
        st.dataframe(result_df.style.applymap(
            lambda x: 'background-color: #d4edda' if isinstance(x, int) and x >= threshold else ''
        ))
        
        # Persiapan download Excel
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            result_df.to_excel(writer, index=False, sheet_name='Hasil')
        
        # Download hasil
        st.download_button(
            label="📥 Download Hasil (Excel)",
            data=buffer.getvalue(),
            file_name="hasil_pencarian_sekolah.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    app()

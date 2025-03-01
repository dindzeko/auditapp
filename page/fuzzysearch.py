import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz

def fuzzy_search_in_target(data_list, target_text, threshold=70):
    """
    Fungsi untuk mencari string dalam teks target dengan toleransi typo.
    Menggunakan kombinasi token_set_ratio dan partial_ratio untuk akurasi lebih baik.
    """
    best_match = None
    best_score = 0
    
    # Preprocessing: Ubah ke lowercase dan hapus spasi berlebih
    target_clean = " ".join(target_text.lower().split())
    
    for item in data_list:
        if not isinstance(item, str):
            continue
            
        item_clean = " ".join(item.lower().split())
        
        # Gunakan kombinasi metrik untuk hasil optimal
        set_ratio = fuzz.token_set_ratio(item_clean, target_clean)
        partial_ratio = fuzz.partial_ratio(item_clean, target_clean)
        score = (set_ratio + partial_ratio) // 2  # Rata-rata kedua metrik
        
        if score > best_score and score >= threshold:
            best_match = item
            best_score = score
            
    return (best_match, best_score) if best_match else (None, None)

def app():
    st.write("Fuzzy Searching dengan penanganan singkatan dan urutan kata")

    # Session state
    if 'data_list' not in st.session_state:
        st.session_state['data_list'] = []
    if 'target_df' not in st.session_state:
        st.session_state['target_df'] = None

    # Upload Data List
    st.subheader("Upload Data List (Kolom: Data)")
    uploaded_data = st.file_uploader("Upload file Excel Data", type=["xlsx", "xls"])
    if uploaded_data:
        try:
            df = pd.read_excel(uploaded_data)
            st.session_state['data_list'] = df['Data'].dropna().str.strip().tolist()
            st.success(f"{len(st.session_state['data_list'])} data terdeteksi")
        except Exception as e:
            st.error(f"Gagal membaca data: {e}")

    # Upload Target
    st.subheader("Upload Target (Kolom: Target)")
    uploaded_target = st.file_uploader("Upload file Excel Target", type=["xlsx", "xls"])
    if uploaded_target:
        try:
            df = pd.read_excel(uploaded_target)
            st.session_state['target_df'] = df
            st.success(f"{len(df)} target terdeteksi")
        except Exception as e:
            st.error(f"Gagal membaca target: {e}")

    # Proses Pencarian
    st.subheader("Eksekusi Pencarian")
    threshold = st.slider("Threshold Kemiripan", 50, 100, 70)
    
    if st.button("Mulai Pencarian"):
        if not st.session_state['data_list']:
            st.warning("Data List belum diupload")
            return
        if st.session_state['target_df'] is None:
            st.warning("Target belum diupload")
            return
        
        # Proses tiap baris di Target
        results = []
        for _, row in st.session_state['target_df'].iterrows():
            target_text = row.get('Target', '')
            if not isinstance(target_text, str):
                results.append((None, None))
                continue
                
            match, score = fuzzy_search_in_target(
                st.session_state['data_list'],
                target_text,
                threshold
            )
            results.append((match, score))
        
        # Tambahkan kolom hasil ke DataFrame
        st.session_state['target_df'] = st.session_state['target_df'].assign(
            **{
                "Hasil Pencarian": [r[0] for r in results],
                "Tingkat Kemiripan": [r[1] for r in results]
            }
        )
        
        # Tampilkan hasil
        st.dataframe(st.session_state['target_df'])
        
        # Download hasil
        df_to_download = st.session_state['target_df']
        csv = df_to_download.to_csv(index=False)
        st.download_button(
            label="Download Hasil",
            data=csv,
            file_name="hasil_pencarian.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    app()

import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
import cv2
import numpy as np
from PIL import Image

# Inisialisasi session state
if 'original_image' not in st.session_state:
    st.session_state.original_image = None
if 'display_image' not in st.session_state:
    st.session_state.display_image = None
if 'ratio' not in st.session_state:
    st.session_state.ratio = 1.0
if 'ref_points' not in st.session_state:
    st.session_state.ref_points = []
if 'polygon_points' not in st.session_state:
    st.session_state.polygon_points = []
if 'distance_points' not in st.session_state:
    st.session_state.distance_points = []
if 'scale' not in st.session_state:
    st.session_state.scale = None
if 'mode' not in st.session_state:
    st.session_state.mode = None

def main():
    st.title("Pengukuran Panjang dan Luas dari Gambar")
    
    # Upload gambar
    uploaded_file = st.file_uploader("Upload Gambar", type=["jpg", "jpeg", "png"])
    
    if uploaded_file is not None:
        # Baca gambar dan konversi ke RGB
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        original_image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        original_image_rgb = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
        
        # Resize untuk ditampilkan
        display_width = 800
        h, w = original_image_rgb.shape[:2]
        ratio = display_width / w
        display_height = int(h * ratio)
        display_image = cv2.resize(original_image_rgb, (display_width, display_height))
        
        # Simpan ke session state
        st.session_state.original_image = original_image_rgb
        st.session_state.display_image = display_image
        st.session_state.ratio = 1/ratio  # Rasio original/display
        
        # Tampilkan gambar dan tangkap koordinat klik
        st.write("Klik pada gambar untuk memilih titik")
        img_pil = Image.fromarray(st.session_state.display_image)
        coordinates = streamlit_image_coordinates(img_pil, key="pil")
        
        if coordinates is not None:
            # Konversi koordinat display ke original
            x_disp = coordinates['x']
            y_disp = coordinates['y']
            x_orig = x_disp * st.session_state.ratio
            y_orig = y_disp * st.session_state.ratio
            
            # Tambahkan titik sesuai mode
            if st.session_state.mode == 'reference':
                st.session_state.ref_points.append((x_orig, y_orig))
                if len(st.session_state.ref_points) == 2:
                    st.session_state.mode = None
                    
            elif st.session_state.mode == 'polygon':
                st.session_state.polygon_points.append((x_orig, y_orig))
                
            elif st.session_state.mode == 'distance':
                st.session_state.distance_points.append((x_orig, y_orig))
                if len(st.session_state.distance_points) == 2:
                    st.session_state.mode = None

        # Gambar annotations pada display image
        display_image = st.session_state.display_image.copy()
        display_image_bgr = cv2.cvtColor(display_image, cv2.COLOR_RGB2BGR)
        
        # Gambar garis referensi
        if st.session_state.ref_points:
            for pt in st.session_state.ref_points:
                x = int(pt[0] / st.session_state.ratio)
                y = int(pt[1] / st.session_state.ratio)
                cv2.circle(display_image_bgr, (x, y), 5, (0,255,0), -1)
            
            if len(st.session_state.ref_points) >= 2:
                x1 = int(st.session_state.ref_points[0][0] / st.session_state.ratio)
                y1 = int(st.session_state.ref_points[0][1] / st.session_state.ratio)
                x2 = int(st.session_state.ref_points[1][0] / st.session_state.ratio)
                y2 = int(st.session_state.ref_points[1][1] / st.session_state.ratio)
                cv2.line(display_image_bgr, (x1,y1), (x2,y2), (0,255,0), 2)
                
                # Hitung skala jika belum ada
                if st.session_state.scale is None:
                    px = np.sqrt((x2-x1)**2 + (y2-y1)**2) * (1/st.session_state.ratio)
                    actual = st.number_input("Masukkan panjang referensi (meter):", 
                                           min_value=0.1, value=1.0)
                    st.session_state.scale = actual / px
                    st.success(f"Skala: {st.session_state.scale:.4f} m/px")

        # Gambar poligon
        if st.session_state.polygon_points:
            for pt in st.session_state.polygon_points:
                x = int(pt[0] / st.session_state.ratio)
                y = int(pt[1] / st.session_state.ratio)
                cv2.circle(display_image_bgr, (x, y), 5, (255,0,0), -1)
            
            if len(st.session_state.polygon_points) >= 2:
                pts = []
                for pt in st.session_state.polygon_points:
                    x = int(pt[0] / st.session_state.ratio)
                    y = int(pt[1] / st.session_state.ratio)
                    pts.append((x,y))
                
                pts = np.array(pts, dtype=np.int32)
                cv2.polylines(display_image_bgr, [pts], True, (255,0,0), 2)
                
                # Hitung luas jika ada skala
                if st.session_state.scale and len(pts) >= 3:
                    area_px = cv2.contourArea(pts * st.session_state.ratio)
                    area = area_px * (st.session_state.scale**2)
                    perimeter = cv2.arcLength(pts * st.session_state.ratio, True) * st.session_state.scale
                    st.success(f"Luas: {area:.2f} m² | Keliling: {perimeter:.2f} m")

        # Gambar jarak
        if st.session_state.distance_points:
            for pt in st.session_state.distance_points:
                x = int(pt[0] / st.session_state.ratio)
                y = int(pt[1] / st.session_state.ratio)
                cv2.circle(display_image_bgr, (x, y), 5, (0,0,255), -1)
            
            if len(st.session_state.distance_points) >= 2:
                x1 = int(st.session_state.distance_points[0][0] / st.session_state.ratio)
                y1 = int(st.session_state.distance_points[0][1] / st.session_state.ratio)
                x2 = int(st.session_state.distance_points[1][0] / st.session_state.ratio)
                y2 = int(st.session_state.distance_points[1][1] / st.session_state.ratio)
                cv2.line(display_image_bgr, (x1,y1), (x2,y2), (0,0,255), 2)
                
                # Hitung jarak jika ada skala
                if st.session_state.scale:
                    px = np.sqrt((x2-x1)**2 + (y2-y1)**2) * (1/st.session_state.ratio)
                    distance = px * st.session_state.scale
                    st.success(f"Jarak: {distance:.2f} m")

        # Tampilkan gambar hasil
        display_image_rgb = cv2.cvtColor(display_image_bgr, cv2.COLOR_BGR2RGB)
        st.image(display_image_rgb)

        # Tombol kontrol
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Tarik Garis Referensi"):
                st.session_state.mode = 'reference'
                st.session_state.ref_points = []
        with col2:
            if st.button("Tarik Poligon"):
                st.session_state.mode = 'polygon'
                st.session_state.polygon_points = []
        with col3:
            if st.button("Ukur Jarak"):
                st.session_state.mode = 'distance'
                st.session_state.distance_points = []

if __name__ == "__main__":
    main()

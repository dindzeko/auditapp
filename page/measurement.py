import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io

def app():
    st.title("Pengukuran Panjang dan Luas dari Gambar")

    # Inisialisasi session state
    if "image" not in st.session_state:
        st.session_state.image = None
    if "resized_image" not in st.session_state:
        st.session_state.resized_image = None
    if "ref_points" not in st.session_state:
        st.session_state.ref_points = []
    if "polygon_points" not in st.session_state:
        st.session_state.polygon_points = []
    if "scale" not in st.session_state:
        st.session_state.scale = None
    if "resize_ratio" not in st.session_state:
        st.session_state.resize_ratio = 1.0
    if "mode" not in st.session_state:
        st.session_state.mode = None

    # Fungsi untuk menghitung jarak antara dua titik
    def calculate_distance(point1, point2):
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

    # Fungsi untuk menghitung luas poligon
    def calculate_polygon_area(points):
        points = np.array(points, dtype=np.int32)
        return cv2.contourArea(points)

    # Upload gambar
    uploaded_file = st.file_uploader("Upload Gambar", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        st.session_state.image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if st.session_state.image is None:
            st.error("Gagal membaca gambar. Pastikan file valid.")
        else:
            # Resize gambar untuk tampilan
            canvas_width = 800
            canvas_height = 600
            original_height, original_width = st.session_state.image.shape[:2]
            width_ratio = canvas_width / original_width
            height_ratio = canvas_height / original_height
            st.session_state.resize_ratio = min(width_ratio, height_ratio)
            new_width = int(original_width * st.session_state.resize_ratio)
            new_height = int(original_height * st.session_state.resize_ratio)
            st.session_state.resized_image = cv2.resize(st.session_state.image, (new_width, new_height))

    # Tangkap klik pengguna dan gambar ulang dengan anotasi
    if st.session_state.resized_image is not None:
        display_image = st.session_state.resized_image.copy()
        
        # Gambar titik referensi
        for point in st.session_state.ref_points:
            x, y = int(point[0]), int(point[1])
            cv2.circle(display_image, (x, y), 5, (0, 0, 255), -1)
        if len(st.session_state.ref_points) == 2:
            pt1 = (int(st.session_state.ref_points[0][0]), int(st.session_state.ref_points[0][1]))
            pt2 = (int(st.session_state.ref_points[1][0]), int(st.session_state.ref_points[1][1]))
            cv2.line(display_image, pt1, pt2, (0, 0, 255), 2)
        
        # Gambar poligon
        if len(st.session_state.polygon_points) > 0:
            for point in st.session_state.polygon_points:
                x, y = int(point[0]), int(point[1])
                cv2.circle(display_image, (x, y), 5, (0, 255, 0), -1)
            if len(st.session_state.polygon_points) >= 2:
                pts = np.array(st.session_state.polygon_points, dtype=np.int32)
                cv2.polylines(display_image, [pts], False, (0, 255, 0), 2)
        
        # Konversi ke format Streamlit
        display_image = cv2.cvtColor(display_image, cv2.COLOR_BGR2RGB)
        st.image(display_image, 
                caption="Gambar dengan Anotasi", 
                use_container_width=True,
                key="canvas")

        # Proses klik pengguna
        if st.session_state.mode and "canvas" in st.session_state:
            click_data = st.session_state.canvas
            if click_data is not None:
                x = click_data["x"]
                y = click_data["y"]
                if st.session_state.mode == "reference":
                    st.session_state.ref_points.append((x, y))
                elif st.session_state.mode == "polygon":
                    st.session_state.polygon_points.append((x, y))
                st.session_state.canvas = None  # Reset klik

    # Mode Referensi
    st.subheader("Langkah 1: Tarik Garis Referensi")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Mulai Mode Referensi"):
            st.session_state.mode = "reference"
            st.session_state.ref_points = []
    with col2:
        if st.button("Selesai Referensi"):
            st.session_state.mode = None
            if len(st.session_state.ref_points) == 2:
                ref_length = calculate_distance(st.session_state.ref_points[0], 
                                              st.session_state.ref_points[1])
                actual_length = st.number_input("Masukkan panjang referensi (meter):", 
                                               value=1.0, 
                                               min_value=0.01)
                st.session_state.scale = actual_length / (ref_length / st.session_state.resize_ratio)
                st.success(f"Skala: {st.session_state.scale:.4f} meter/piksel")
            else:
                st.warning("Tarik garis dengan 2 titik terlebih dahulu!")

    # Mode Poligon
    st.subheader("Langkah 2: Tarik Poligon untuk Area")
    col3, col4 = st.columns(2)
    with col3:
        if st.button("Mulai Mode Poligon"):
            st.session_state.mode = "polygon"
            st.session_state.polygon_points = []
    with col4:
        if st.button("Selesai Poligon"):
            st.session_state.mode = None
            if len(st.session_state.polygon_points) >= 3:
                # Hitung luas dan keliling
                area_pixels = calculate_polygon_area(st.session_state.polygon_points)
                perimeter_pixels = 0
                points = st.session_state.polygon_points + [st.session_state.polygon_points[0]]
                for i in range(len(points)-1):
                    perimeter_pixels += calculate_distance(points[i], points[i+1])
                
                # Konversi ke satuan nyata
                area_real = area_pixels * (st.session_state.scale**2) / (st.session_state.resize_ratio**2)
                perimeter_real = perimeter_pixels * st.session_state.scale / st.session_state.resize_ratio
                
                st.subheader("Hasil Perhitungan:")
                st.metric("Luas Area", f"{area_real:.2f} m²")
                st.metric("Keliling Area", f"{perimeter_real:.2f} m")
            else:
                st.warning("Poligon membutuhkan minimal 3 titik!")

    # Reset semua
    if st.button("Reset Semua"):
        st.session_state.image = None
        st.session_state.resized_image = None
        st.session_state.ref_points = []
        st.session_state.polygon_points = []
        st.session_state.scale = None
        st.session_state.mode = None
        st.experimental_rerun()

if __name__ == "__main__":
    app()

import streamlit as st
import cv2
import numpy as np
from PIL import Image
from streamlit_drawable_canvas import st_canvas

def app():
    st.title("Pengukuran Panjang dan Luas dari Gambar")

    # Inisialisasi session state
    if "image" not in st.session_state:
        st.session_state["image"] = None
    if "resized_image" not in st.session_state:
        st.session_state["resized_image"] = None
    if "ref_points" not in st.session_state:
        st.session_state["ref_points"] = []
    if "polygon_points" not in st.session_state:
        st.session_state["polygon_points"] = []
    if "scale" not in st.session_state:
        st.session_state["scale"] = None
    if "resize_ratio" not in st.session_state:
        st.session_state["resize_ratio"] = 1.0

    # Fungsi untuk menghitung jarak antara dua titik
    def calculate_distance(point1, point2):
        return np.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

    # Fungsi untuk menghitung luas poligon
    def calculate_polygon_area(points):
        points = np.array(points, dtype=np.int32)
        return cv2.contourArea(points)

    # Upload gambar
    uploaded_file = st.file_uploader("Upload Gambar", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        # Baca gambar menggunakan OpenCV
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        st.session_state["image"] = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if st.session_state["image"] is None:
            st.error("Gagal membaca gambar. Pastikan file valid.")
        else:
            # Resize gambar agar sesuai dengan tampilan Streamlit
            canvas_width = 800
            canvas_height = 600
            original_height, original_width = st.session_state["image"].shape[:2]
            width_ratio = canvas_width / original_width
            height_ratio = canvas_height / original_height
            st.session_state["resize_ratio"] = min(width_ratio, height_ratio)
            new_width = int(original_width * st.session_state["resize_ratio"])
            new_height = int(original_height * st.session_state["resize_ratio"])
            st.session_state["resized_image"] = cv2.resize(st.session_state["image"], (new_width, new_height))

            # Tampilkan gambar di Streamlit
            image_rgb = cv2.cvtColor(st.session_state["resized_image"], cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(image_rgb)
            st.image(pil_image, caption="Gambar yang Diupload", use_container_width=True)

    # Mode Referensi
    st.subheader("Langkah 1: Tarik Garis Referensi")
    if st.button("Mulai Mode Referensi"):
        st.write("Klik dua titik pada gambar untuk menarik garis referensi.")
        st.session_state["ref_points"] = []

    # Canvas untuk mode referensi
    if st.session_state["image"] is not None:
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",  # Warna transparan
            stroke_width=2,
            stroke_color="#FF0000",
            background_image=Image.fromarray(cv2.cvtColor(st.session_state["resized_image"], cv2.COLOR_BGR2RGB)),
            update_streamlit=True,
            height=600,
            drawing_mode="line",
            key="canvas_ref",
        )

        if canvas_result.json_data and len(canvas_result.json_data["objects"]) > 0:
            ref_points = [
                (int(obj["left"]), int(obj["top"])) for obj in canvas_result.json_data["objects"]
            ]
            st.session_state["ref_points"] = ref_points

    if st.button("Selesai Referensi"):
        ref_points = st.session_state["ref_points"]
        if len(ref_points) == 2:
            ref_length_pixels = calculate_distance(ref_points[0], ref_points[1]) / st.session_state["resize_ratio"]
            actual_length_meters = st.number_input("Masukkan panjang garis referensi dalam meter:", value=1.0)
            st.session_state["scale"] = actual_length_meters / ref_length_pixels
            st.success(f"Skala: {st.session_state['scale']:.6f} meter per piksel")
        else:
            st.warning("Garis referensi tidak valid. Minimal 2 titik diperlukan.")

    # Mode Poligon
    st.subheader("Langkah 2: Tarik Poligon untuk Area")
    if st.button("Mulai Mode Poligon"):
        st.write("Klik untuk menambahkan titik-titik poligon. Tekan tombol 'Selesai' untuk menyelesaikan.")
        st.session_state["polygon_points"] = []

    # Canvas untuk mode poligon
    if st.session_state["image"] is not None:
        canvas_result = st_canvas(
            fill_color="rgba(0, 255, 0, 0.3)",  # Warna transparan
            stroke_width=2,
            stroke_color="#00FF00",
            background_image=Image.fromarray(cv2.cvtColor(st.session_state["resized_image"], cv2.COLOR_BGR2RGB)),
            update_streamlit=True,
            height=600,
            drawing_mode="polygon",
            key="canvas_polygon",
        )

        if canvas_result.json_data and len(canvas_result.json_data["objects"]) > 0:
            polygon_points = [
                (int(point["x"]), int(point["y"])) for point in canvas_result.json_data["objects"][0]["path"][:-1]
            ]
            st.session_state["polygon_points"] = polygon_points

    if st.button("Selesai Poligon"):
        polygon_points = st.session_state["polygon_points"]
        if len(polygon_points) >= 3:
            polygon_area_pixels = calculate_polygon_area(polygon_points) / (st.session_state["resize_ratio"] ** 2)
            polygon_area_meters = polygon_area_pixels * (st.session_state["scale"] ** 2)
            total_length_pixels = sum(
                calculate_distance(polygon_points[i], polygon_points[i + 1])
                for i in range(len(polygon_points) - 1)
            ) / st.session_state["resize_ratio"]
            total_length_meters = total_length_pixels * st.session_state["scale"]
            st.write(f"Luas Area: {polygon_area_meters:.2f} m²")
            st.write(f"Panjang Total: {total_length_meters:.2f} m")
        else:
            st.warning("Poligon tidak valid. Minimal 3 titik diperlukan.")

if __name__ == "__main__":
    app()

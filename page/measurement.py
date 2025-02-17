import streamlit as st
import cv2
import numpy as np
from PIL import Image

def app():
    st.title("Pengukuran Panjang dan Luas dari Gambar")

    # Inisialisasi session state
    if "image" not in st.session_state:
        st.session_state["image"] = None
    if "resized_image" not in st.session_state:
        st.session_state["resized_image"] = None
    if "ref_points" not in st.session_state:
        st.session_state["ref_points"] = []
    if "scale" not in st.session_state:
        st.session_state["scale"] = None
    if "resize_ratio" not in st.session_state:
        st.session_state["resize_ratio"] = 1.0

    def calculate_distance(point1, point2):
        return np.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

    uploaded_file = st.file_uploader("Upload Gambar", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
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

    if st.session_state["resized_image"] is not None:
        st.subheader("Klik pada gambar untuk memilih titik referensi")

        # Gambar titik referensi pada gambar
        img_copy = st.session_state["resized_image"].copy()
        for point in st.session_state["ref_points"]:
            cv2.circle(img_copy, point, radius=5, color=(0, 0, 255), thickness=-1)  # Titik merah

        # Konversi gambar ke RGB untuk Streamlit
        image_rgb = cv2.cvtColor(img_copy, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(image_rgb)
        st.image(pil_image, use_container_width=True)

        # Ambil koordinat dengan slider atau input
        x = st.slider("Pilih X", 0, new_width, step=1)
        y = st.slider("Pilih Y", 0, new_height, step=1)

        if st.button("Tambahkan Titik Referensi"):
            if len(st.session_state["ref_points"]) < 2:
                st.session_state["ref_points"].append((x, y))
            else:
                st.warning("Sudah ada dua titik referensi. Reset untuk memilih ulang.")

        if st.button("Reset Titik"):
            st.session_state["ref_points"] = []

        if len(st.session_state["ref_points"]) == 2:
            ref_length_pixels = calculate_distance(
                st.session_state["ref_points"][0], st.session_state["ref_points"][1]
            ) / st.session_state["resize_ratio"]
            actual_length_meters = st.number_input("Masukkan panjang garis referensi dalam meter:", value=1.0)
            st.session_state["scale"] = actual_length_meters / ref_length_pixels
            st.success(f"Skala: {st.session_state['scale']:.6f} meter per piksel")

if __name__ == "__main__":
    app()

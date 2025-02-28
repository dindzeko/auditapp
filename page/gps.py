import streamlit as st
from exif import Image as ExifImage
import io
from PIL import Image
import pillow_heif
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import simplekml

def extract_coordinates(image_bytes):
    """
    Fungsi untuk mengekstrak koordinat GPS dari gambar.
    Parameters:
        image_bytes (bytes): Data gambar dalam bentuk bytes.
    Returns:
        tuple: Koordinat (latitude, longitude) atau None jika tidak ada data GPS.
    """
    try:
        # Verifikasi apakah gambar valid
        Image.open(io.BytesIO(image_bytes)).verify()
    except Exception:
        return None
    
    # Konversi HEIC ke JPEG jika diperlukan
    if image_bytes.startswith(b"ftypheic"):
        image_bytes = convert_heic_to_jpeg(image_bytes)
        if not image_bytes:
            return None

    try:
        img = ExifImage(image_bytes)
    except Exception:
        return None

    # Periksa apakah metadata GPS tersedia
    if not hasattr(img, 'gps_latitude'):
        return None

    # Ekstrak koordinat GPS
    lat = img.gps_latitude
    lon = img.gps_longitude
    lat_ref = img.gps_latitude_ref
    lon_ref = img.gps_longitude_ref

    lat_decimal = lat[0] + lat[1] / 60 + lat[2] / 3600
    if lat_ref != 'N':
        lat_decimal = -lat_decimal

    lon_decimal = lon[0] + lon[1] / 60 + lon[2] / 3600
    if lon_ref != 'E':
        lon_decimal = -lon_decimal

    return (lat_decimal, lon_decimal)

def convert_heic_to_jpeg(image_bytes):
    """
    Fungsi untuk mengonversi gambar HEIC ke format JPEG.
    Parameters:
        image_bytes (bytes): Data gambar HEIC dalam bentuk bytes.
    Returns:
        bytes: Data gambar JPEG atau None jika gagal.
    """
    try:
        heif_file = pillow_heif.read_heif(image_bytes)
        image = Image.frombytes(
            heif_file.mode,
            heif_file.size,
            heif_file.data,
            "raw"
        )
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=90)
        return img_byte_arr.getvalue()
    except Exception as e:
        st.error(f"Gagal konversi HEIC: {str(e)}")
        return None

def app():
    """
    Fungsi utama untuk halaman GPS Google Earth.
    """
    st.markdown('<div class="fade-in main-content">', unsafe_allow_html=True)
    st.title("🌍 GPS Tools")
    st.write("""
    Halaman ini memungkinkan Anda mengunggah foto dengan data GPS, mengekstrak koordinatnya, 
    dan menampilkan lokasi di peta interaktif. Anda juga dapat mengunduh file KML untuk digunakan di Google Earth.
    """)

    # Upload multiple gambar
    uploaded_files = st.file_uploader(
        "Upload Foto (JPG/HEIC)",
        type=['jpg', 'jpeg', 'heic'],
        accept_multiple_files=True
    )

    # Proses gambar
    coordinates = []
    valid_data = []

    for uploaded_file in uploaded_files:
        bytes_data = uploaded_file.getvalue()
        coords = extract_coordinates(bytes_data)
        
        if coords:
            # Simpan data
            coordinates.append(coords)
            valid_data.append({
                "Nama File": uploaded_file.name,
                "Latitude": coords[0],
                "Longitude": coords[1]
            })
        else:
            st.warning(f"Foto {uploaded_file.name} tidak memiliki data GPS")

    # Tampilkan hasil
    if coordinates:
        # Tampilkan tabel hasil
        st.subheader("📊 Data Foto dengan Koordinat GPS")
        df = pd.DataFrame(valid_data)
        st.dataframe(df.style.format({"Latitude": "{:.6f}", "Longitude": "{:.6f}"}))
        
        # Informasi jumlah foto yang berhasil diproses
        st.info(f"Total foto dengan data GPS yang berhasil diproses: {len(valid_data)}")
        
        # Buat peta dengan marker diurutkan berdasarkan urutan upload
        m = folium.Map(location=coordinates[0], zoom_start=14)
        marker_cluster = MarkerCluster().add_to(m)
        
        for row in valid_data:
            coord = (row["Latitude"], row["Longitude"])
            filename = row["Nama File"]
            
            folium.Marker(
                location=coord,
                popup=filename,
                tooltip=filename
            ).add_to(marker_cluster)
        
        # Tampilkan peta
        st.subheader("📍 Peta Lokasi Foto")
        st_folium(m, width=700, height=500)
        
        # Download KML
        kml = simplekml.Kml()
        for row in valid_data:
            coord = (row["Latitude"], row["Longitude"])
            filename = row["Nama File"]
            kml.newpoint(
                name=filename,
                coords=[(coord[1], coord[0])]
            )
        kml_file = kml.kml().encode('utf-8')
        
        st.download_button(
            label="📥 Download KML",
            data=kml_file,
            file_name="lokasi_foto.kml",
            mime="application/vnd.google-earth.kml+xml"
        )
    else:
        st.info("Silakan upload foto dengan data GPS.")

    st.markdown('</div>', unsafe_allow_html=True)

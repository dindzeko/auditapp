import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

class AHPApp:
    def __init__(self):
        self.criteria_names = []
        self.comparisons = []
        self.added_pairs = set()
        self.criteria_list = []

    def initialize_gui(self):
        # Initialize session state variables
        if "criteria_names" not in st.session_state:
            st.session_state["criteria_names"] = []
        if "criteria_list" not in st.session_state:
            st.session_state["criteria_list"] = []
        if "comparisons" not in st.session_state:
            st.session_state["comparisons"] = []
        if "added_pairs" not in st.session_state:
            st.session_state["added_pairs"] = set()

        st.title("AHP - Analytical Hierarchy Process")
        st.markdown("""
        **Instruksi:**
        1. Masukkan jumlah kriteria.
        2. Isi nama kriteria.
        3. Tambahkan perbandingan antar kriteria.
        4. Hitung prioritas dan konsistensi.
        """)

        # Input jumlah kriteria
        num_criteria = st.number_input(
            "Jumlah Kriteria", 
            min_value=1,  # Minimum value is 1
            max_value=10,  # Maximum value is 10
            value=2,       # Default value is 2
            step=1         # Increment by 1
        )
        if st.button("Buat Kriteria"):
            if num_criteria < 1 or num_criteria > 10:
                st.error("Jumlah kriteria harus berada antara 1 dan 10.")
            else:
                self.criteria_names = [f"Kriteria {i+1}" for i in range(num_criteria)]
                self.criteria_list = []
                self.comparisons = []
                self.added_pairs = set()
                st.session_state["criteria_names"] = self.criteria_names
                st.rerun()  # Use st.rerun() instead of st.experimental_rerun()

        # Tampilkan input nama kriteria jika sudah dibuat
        if "criteria_names" in st.session_state and st.session_state["criteria_names"]:
            self.criteria_list = []
            st.subheader("Nama Kriteria")
            for i, name in enumerate(st.session_state["criteria_names"]):
                crit_name = st.text_input(f"Nama Kriteria {i+1}", value=name)
                self.criteria_list.append(crit_name.strip())
            if st.button("Lanjut ke Perbandingan"):
                if all(self.criteria_list):
                    st.session_state["criteria_list"] = self.criteria_list
                    st.session_state["comparisons"] = []
                    st.session_state["added_pairs"] = set()
                    st.rerun()  # Use st.rerun() instead of st.experimental_rerun()
                else:
                    st.error("Semua nama kriteria harus diisi.")

        # Tampilkan input perbandingan jika kriteria sudah ditentukan
        if "criteria_list" in st.session_state and st.session_state["criteria_list"]:
            self.criteria_list = st.session_state["criteria_list"]
            self.comparisons = st.session_state.get("comparisons", [])
            self.added_pairs = st.session_state.get("added_pairs", set())

            # Display comparison list with delete buttons
            if self.comparisons:
                st.subheader("Daftar Perbandingan")
                for i, comp in enumerate(self.comparisons):
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.write(f"{comp['a']} vs {comp['b']}: Skala {comp['scale']}, Lebih Penting: {comp['more']}")
                    with col2:
                        if st.button(f"Hapus {i}", key=f"delete_{i}"):
                            # Remove the comparison
                            pair = frozenset({comp["a"], comp["b"]})
                            self.comparisons.pop(i)
                            self.added_pairs.remove(pair)
                            st.session_state["comparisons"] = self.comparisons
                            st.session_state["added_pairs"] = self.added_pairs
                            st.rerun()

            # Add new comparison
            st.subheader("Tambah Perbandingan Baru")
            col1, col2, col3 = st.columns(3)
            with col1:
                crit_a = st.selectbox("Kriteria A", self.criteria_list)
            with col2:
                crit_b = st.selectbox("Kriteria B", [c for c in self.criteria_list if c != crit_a])
            with col3:
                scale = st.selectbox("Skala Keutamaan", list(range(1, 10)))
            more_important = st.radio("Mana yang lebih penting?", [crit_a, crit_b])
            if st.button("Tambah Perbandingan"):
                pair = frozenset({crit_a, crit_b})
                if pair in self.added_pairs:
                    st.error("Perbandingan ini sudah ada.")
                else:
                    self.added_pairs.add(pair)
                    self.comparisons.append({
                        "a": crit_a,
                        "b": crit_b,
                        "more": more_important,
                        "scale": scale
                    })
                    st.session_state["comparisons"] = self.comparisons
                    st.session_state["added_pairs"] = self.added_pairs
                    st.rerun()  # Use st.rerun() instead of st.experimental_rerun()

            # Tombol hitung
            if st.button("Hitung Prioritas"):
                self.calculate()

    def calculate(self):
        try:
            n = len(self.criteria_list)
            required = n * (n - 1) // 2
            if len(self.added_pairs) != required:
                st.error(f"Perlu {required} perbandingan unik.")
                return
            matrix = np.ones((n, n))
            for comp in self.comparisons:
                i = self.criteria_list.index(comp["a"])
                j = self.criteria_list.index(comp["b"])
                scale = comp["scale"]
                if comp["more"] == comp["a"]:
                    matrix[i][j] = scale
                    matrix[j][i] = 1 / scale
                else:
                    matrix[i][j] = 1 / scale
                    matrix[j][i] = scale
            normalized = matrix / matrix.sum(axis=0)
            weights = normalized.mean(axis=1)
            lambda_max = np.sum(matrix.dot(weights) / weights) / n
            CI = (lambda_max - n) / (n - 1)
            RI = {1: 0, 2: 0, 3: 0.58, 4: 0.9, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}.get(n, 1.49)
            CR = CI / RI

            # Store results
            priority_df = pd.DataFrame({"Kriteria": self.criteria_list, "Bobot": weights})

            # Display results
            st.subheader("Hasil Perhitungan")
            st.write("Matriks Perbandingan:")
            st.dataframe(pd.DataFrame(matrix, columns=self.criteria_list, index=self.criteria_list))
            st.write("Prioritas Kriteria:")
            st.dataframe(priority_df)
            st.write(f"Consistency Ratio (CR): {CR:.4f}")
            if CR < 0.1:
                st.success("Konsisten (CR < 0.1)")
            else:
                st.error("Tidak Konsisten (CR >= 0.1)")

            # Visualizations
            self.visualize_results(priority_df, matrix)
        except Exception as e:
            st.error(f"Error: {str(e)}")

    def visualize_results(self, priority_df, matrix):
        st.subheader("Visualisasi Hasil")
        # 1. Bar Chart
        st.write("Bar Chart Prioritas Kriteria:")
        fig, ax = plt.subplots()
        ax.barh(priority_df["Kriteria"], priority_df["Bobot"], color="skyblue")
        ax.set_xlabel("Bobot")
        ax.set_title("Prioritas Kriteria")
        st.pyplot(fig)

        # 2. Pie Chart
        st.write("Pie Chart Proporsi Prioritas:")
        fig, ax = plt.subplots()
        ax.pie(priority_df["Bobot"], labels=priority_df["Kriteria"], autopct="%1.1f%%", startangle=90)
        ax.set_title("Proporsi Prioritas Kriteria")
        st.pyplot(fig)

        # 3. Heatmap
        st.write("Heatmap Matriks Perbandingan:")
        fig, ax = plt.subplots()
        sns.heatmap(matrix, annot=True, cmap="coolwarm", xticklabels=self.criteria_list, yticklabels=self.criteria_list, ax=ax)
        ax.set_title("Heatmap Matriks Perbandingan")
        st.pyplot(fig)

        # 4. Radar Chart
        st.write("Radar Chart Prioritas Kriteria:")
        fig = px.line_polar(priority_df, r="Bobot", theta="Kriteria", line_close=True)
        fig.update_traces(fill='toself')
        st.plotly_chart(fig)

        # 5. Line Chart
        st.write("Line Chart Prioritas Kriteria:")
        fig, ax = plt.subplots()
        ax.plot(priority_df["Kriteria"], priority_df["Bobot"], marker="o", color="green")
        ax.set_title("Line Chart Prioritas Kriteria")
        ax.set_ylabel("Bobot")
        st.pyplot(fig)


def app():
    app_instance = AHPApp()
    app_instance.initialize_gui()

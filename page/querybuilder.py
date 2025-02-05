import streamlit as st

class SQLSimulatorStreamlit:
    def __init__(self):
        # Inisialisasi state jika belum ada
        if "step" not in st.session_state:
            st.session_state.step = 0  # Step 0: Input jumlah tabel
        if "tables" not in st.session_state:
            st.session_state.tables = []
        if "joins" not in st.session_state:
            st.session_state.joins = []
        if "select_columns" not in st.session_state:
            st.session_state.select_columns = {}
        if "where_conditions" not in st.session_state:
            st.session_state.where_conditions = []
        if "group_by" not in st.session_state:
            st.session_state.group_by = ""
        if "having_conditions" not in st.session_state:
            st.session_state.having_conditions = ""
        if "order_by" not in st.session_state:
            st.session_state.order_by = ""
        if "distinct" not in st.session_state:
            st.session_state.distinct = False

    def initialize_table_input(self):
        st.title("SQL Query Simulator")
        if st.session_state.step == 0:
            num_tables = st.number_input("Jumlah Tabel:", min_value=1, value=1, step=1)
            if st.button("Submit Jumlah Tabel"):
                st.session_state.num_tables = num_tables
                st.session_state.step = 1  # Lanjut ke langkah berikutnya
                st.rerun()  # Refresh halaman untuk melanjutkan ke langkah berikutnya

    def show_table_details(self):
        if st.session_state.step == 1:
            st.subheader("Detail Tabel")
            table_entries = []
            for i in range(st.session_state.num_tables):
                st.write(f"Tabel {i+1}")
                name = st.text_input(f"Nama Tabel {i+1}", key=f"table_name_{i}")
                cols = st.text_input(f"Kolom (pisahkan koma) untuk Tabel {i+1}", key=f"table_cols_{i}")
                table_entries.append({"name": name.strip(), "columns": [c.strip() for c in cols.split(",") if c.strip()]})
            
            if st.button("Submit Detail Tabel"):
                # Validasi input tabel
                valid_tables = [entry for entry in table_entries if entry["name"] and entry["columns"]]
                if len(valid_tables) != st.session_state.num_tables:
                    st.error("Semua tabel harus memiliki nama dan setidaknya satu kolom.")
                    return
                
                st.session_state.tables = valid_tables
                st.session_state.step = 2  # Lanjut ke langkah berikutnya
                st.rerun()  # Refresh halaman untuk melanjutkan ke langkah berikutnya

    def show_join_options(self):
        if st.session_state.step == 2:
            st.subheader("Join Options")
            join_entries = []

            # Tampilkan kotak dengan daftar tabel dan kolom
            st.write("Daftar Tabel dan Kolom:")
            for table in st.session_state.tables:
                with st.expander(f"{table['name']}"):
                    st.write(", ".join(table['columns']))

            # Pilih tabel dan kolom untuk join
            for i in range(len(st.session_state.tables) - 1):
                st.write(f"Join antara Tabel {i + 1} dan {i + 2}")
                
                # Pilih tabel pertama
                table1 = st.selectbox(
                    f"Pilih Tabel Pertama untuk Join {i + 1}",
                    [table['name'] for table in st.session_state.tables],
                    key=f"join_table1_{i}"
                )
                # Cari kolom untuk tabel pertama
                table1_columns = []
                for table in st.session_state.tables:
                    if table['name'] == table1:
                        table1_columns = table['columns']
                        break

                if not table1_columns:
                    st.error(f"Tidak ditemukan kolom untuk tabel '{table1}'. Silakan periksa input tabel.")
                    return

                col1 = st.selectbox(
                    f"Pilih Kolom dari Tabel {table1}",
                    table1_columns,
                    key=f"join_col1_{i}"
                )

                # Pilih tabel kedua
                table2 = st.selectbox(
                    f"Pilih Tabel Kedua untuk Join {i + 1}",
                    [table['name'] for table in st.session_state.tables],
                    key=f"join_table2_{i}"
                )
                # Cari kolom untuk tabel kedua
                table2_columns = []
                for table in st.session_state.tables:
                    if table['name'] == table2:
                        table2_columns = table['columns']
                        break

                if not table2_columns:
                    st.error(f"Tidak ditemukan kolom untuk tabel '{table2}'. Silakan periksa input tabel.")
                    return

                col2 = st.selectbox(
                    f"Pilih Kolom dari Tabel {table2}",
                    table2_columns,
                    key=f"join_col2_{i}"
                )

                join_type = st.selectbox(
                    f"Jenis Join untuk Tabel {i + 1} dan {i + 2}",
                    ["INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN"],
                    key=f"join_type_{i}"
                )
                join_entries.append({
                    "type": join_type,
                    "condition": f"{table1}.{col1} = {table2}.{col2}"
                })

            if st.button("Submit Join Options"):
                st.session_state.joins = join_entries
                st.session_state.step = 3  # Lanjut ke langkah berikutnya
                st.rerun()  # Refresh halaman untuk melanjutkan ke langkah berikutnya

    def show_query_options(self):
        if st.session_state.step == 3:
            st.subheader("Query Options")
            tab_select, tab_where, tab_group, tab_order = st.tabs(["SELECT", "WHERE", "GROUP BY/HAVING", "ORDER BY"])

            with tab_select:
                st.session_state.distinct = st.checkbox("DISTINCT")
                select_vars = {}
                for table in st.session_state.tables:
                    st.write(f"Tabel {table['name']}:")
                    for col in table['columns']:
                        full_name = f"{table['name']}.{col}"
                        aggregation = st.selectbox(
                            f"Pilih Agregasi untuk Kolom {col}",
                            ["None", "SUM", "COUNT", "AVG", "MIN", "MAX"],
                            key=f"agg_{full_name}"
                        )
                        alias = st.text_input(f"Alias untuk Kolom {col} (opsional)", key=f"alias_{full_name}")
                        if aggregation != "None":
                            full_name = f"{aggregation}({full_name})"
                            if alias:
                                full_name += f" AS {alias}"
                        elif alias:
                            full_name += f" AS {alias}"
                        select_vars[full_name] = st.checkbox(col, key=f"select_{full_name}")
                st.session_state.select_columns = select_vars

            with tab_where:
                where_conditions = []
                columns = self.get_all_columns()
                num_conditions = st.number_input("Jumlah Kondisi WHERE:", min_value=0, value=0, step=1)
                for i in range(num_conditions):
                    col = st.selectbox(f"Kolom untuk kondisi WHERE {i+1}", columns, key=f"where_col_{i}")
                    op = st.selectbox(
                        f"Operator untuk kondisi WHERE {i+1}",
                        ["=", "!=", ">", "<", ">=", "<=", "LIKE"],
                        key=f"where_op_{i}"
                    )
                    val = st.text_input(f"Nilai untuk kondisi WHERE {i+1}", key=f"where_val_{i}")
                    condition = f"{col} {op} {val}"
                    if i > 0:
                        logic_operator = st.selectbox(
                            f"Logika untuk kondisi WHERE {i+1}",
                            ["AND", "OR"],
                            key=f"logic_op_{i}"
                        )
                        condition = f" {logic_operator} {condition}"
                    where_conditions.append(condition)
                st.session_state.where_conditions = where_conditions

            with tab_group:
                st.session_state.group_by = st.text_input("GROUP BY (pisahkan koma):")
                st.session_state.having_conditions = st.text_input("HAVING:")

            with tab_order:
                st.session_state.order_by = st.text_input("ORDER BY (pisahkan koma):")

            if st.button("Generate SQL"):
                self.generate_sql()

    def generate_sql(self):
        select = "SELECT "
        if st.session_state.distinct:
            select += "DISTINCT "
        
        selected = [col for col, var in st.session_state.select_columns.items() if var]
        select += ", ".join(selected) if selected else "*"
        
        from_clause = f"\nFROM {st.session_state.tables[0]['name']}"
        for i, join in enumerate(st.session_state.joins):
            from_clause += f"\n{join['type']} {st.session_state.tables[i+1]['name']} ON {join['condition']}"
        
        where = ""
        if st.session_state.where_conditions:
            where = "\nWHERE " + "".join(st.session_state.where_conditions)
        
        group = ""
        if st.session_state.group_by:
            group = f"\nGROUP BY {st.session_state.group_by}"
        
        having = ""
        if st.session_state.having_conditions:
            having = f"\nHAVING {st.session_state.having_conditions}"
        
        order = ""
        if st.session_state.order_by:
            order = f"\nORDER BY {st.session_state.order_by}"
        
        sql = select + from_clause + where + group + having + order
        
        st.subheader("Hasil Query SQL")
        st.code(sql, language="sql")

    def get_all_columns(self):
        return [f"{table['name']}.{col}" for table in st.session_state.tables for col in table['columns']]

# Fungsi app() untuk multipage Streamlit
def app():
    app_instance = SQLSimulatorStreamlit()
    
    # Jalankan langkah-langkah sesuai state
    if st.session_state.step == 0:
        app_instance.initialize_table_input()
    elif st.session_state.step == 1:
        app_instance.show_table_details()
    elif st.session_state.step == 2:
        app_instance.show_join_options()
    elif st.session_state.step == 3:
        app_instance.show_query_options()

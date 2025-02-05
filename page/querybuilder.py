import streamlit as st

class SQLSimulatorStreamlit:
    def __init__(self):
        # Inisialisasi state jika belum ada
        if "tables" not in st.session_state:
            st.session_state.tables = []
        if "joins" not in st.session_state:
            st.session_state.joins = []
        if "select_columns" not in st.session_state:
            st.session_state.select_columns = []
        if "where_conditions" not in st.session_state:
            st.session_state.where_conditions = []
        if "group_by" not in st.session_state:
            st.session_state.group_by = []
        if "having_conditions" not in st.session_state:
            st.session_state.having_conditions = []
        if "order_by" not in st.session_state:
            st.session_state.order_by = []
        if "distinct" not in st.session_state:
            st.session_state.distinct = False

    def initialize_table_input(self):
        st.title("SQL Query Simulator")
        num_tables = st.number_input("Jumlah Tabel:", min_value=1, value=1, step=1)
        if st.button("Submit Jumlah Tabel"):
            # Reset state untuk tabel baru
            st.session_state.tables = []
            self.show_table_details(int(num_tables))

    def show_table_details(self, num_tables):
        st.subheader("Detail Tabel")
        table_entries = []
        for i in range(num_tables):
            st.write(f"Tabel {i+1}")
            name = st.text_input(f"Nama Tabel {i+1}", key=f"table_name_{i}")
            cols = st.text_input(f"Kolom (pisahkan koma) untuk Tabel {i+1}", key=f"table_cols_{i}")
            table_entries.append({"name": name.strip(), "columns": [c.strip() for c in cols.split(",") if c.strip()]})
        
        if st.button("Submit Detail Tabel"):
            # Simpan tabel ke session state
            st.session_state.tables = [entry for entry in table_entries if entry["name"] and entry["columns"]]
            self.show_join_options()

    def show_join_options(self):
        st.subheader("Join Options")
        join_entries = []
        for i in range(len(st.session_state.tables)-1):
            st.write(f"Join antara Tabel {i+1} dan {i+2}")
            join_type = st.selectbox(f"Jenis Join untuk Tabel {i+1} dan {i+2}", 
                                     ["INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN"], 
                                     key=f"join_type_{i}")
            on_condition = st.text_input(f"Kondisi ON untuk Tabel {i+1} dan {i+2}", key=f"on_condition_{i}")
            join_entries.append({"type": join_type, "condition": on_condition})
        
        if st.button("Submit Join Options"):
            # Simpan join ke session state
            st.session_state.joins = join_entries
            self.show_query_options()

    def show_query_options(self):
        st.subheader("Query Options")
        tab_select, tab_where, tab_group, tab_order = st.tabs(["SELECT", "WHERE", "GROUP BY/HAVING", "ORDER BY"])

        with tab_select:
            st.session_state.distinct = st.checkbox("DISTINCT")
            select_vars = {}
            for table in st.session_state.tables:
                st.write(f"Tabel {table['name']}:")
                for col in table['columns']:
                    full_name = f"{table['name']}.{col}"
                    select_vars[full_name] = st.checkbox(col, key=f"select_{full_name}")
            st.session_state.select_columns = select_vars

        with tab_where:
            where_conditions = []
            columns = self.get_all_columns()
            num_conditions = st.number_input("Jumlah Kondisi WHERE:", min_value=0, value=0, step=1)
            for i in range(num_conditions):
                col = st.selectbox(f"Kolom untuk kondisi WHERE {i+1}", columns, key=f"where_col_{i}")
                op = st.selectbox(f"Operator untuk kondisi WHERE {i+1}", 
                                  ["=", "!=", ">", "<", ">=", "<=", "LIKE", "BETWEEN", "IN"], 
                                  key=f"where_op_{i}")
                val = st.text_input(f"Nilai untuk kondisi WHERE {i+1}", key=f"where_val_{i}")
                where_conditions.append(f"{col} {op} {val}")
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
            where = "\nWHERE " + " AND ".join(st.session_state.where_conditions)
        
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
    app_instance.initialize_table_input()

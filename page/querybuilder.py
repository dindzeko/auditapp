import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

class SQLSimulatorStreamlit:
    def __init__(self):
        if "step" not in st.session_state:
            st.session_state.step = 0
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
                st.session_state.step = 1
                st.rerun()

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
                st.session_state.tables = [entry for entry in table_entries if entry["name"] and entry["columns"]]
                st.session_state.step = 2
                st.rerun()

    def show_join_options(self):
        if st.session_state.step == 2:
            st.subheader("Pengurutan Tabel (Drag-and-Drop)")
            
            # Membuat DataFrame untuk tabel
            tables_df = pd.DataFrame([
                {'Tabel': table['name'], 'Kolom': ', '.join(table['columns'])}
                for table in st.session_state.tables
            ])
            
            # Konfigurasi AgGrid untuk drag-and-drop
            gb = GridOptionsBuilder.from_dataframe(tables_df)
            gb.configure_selection()
            gb.configure_grid_options(
                rowDragManaged=True, 
                suppressRowDrag=False, 
                animateRows=True,
                enableRowGroup=False
            )
            gb.configure_column("Tabel", editable=False)
            gb.configure_column("Kolom", editable=False)
            grid_options = gb.build()
            
            grid_response = AgGrid(
                tables_df,
                gridOptions=grid_options,
                update_mode=GridUpdateMode.MODEL_CHANGED,
                fit_columns_on_grid_load=True,
                height=200,
                key='tables_grid'
            )
            
            # Update urutan tabel jika ada perubahan
            if st.button("Simpan Urutan Tabel"):
                new_order = [row['Tabel'] for row in grid_response['data'].to_dict('records')]
                st.session_state.tables = sorted(
                    st.session_state.tables,
                    key=lambda x: new_order.index(x['name'])
                )
                st.success("Urutan tabel berhasil disimpan!")
                st.rerun()

            st.subheader("Konfigurasi Join")
            join_entries = []
            
            for i in range(len(st.session_state.tables)-1):
                table1 = st.session_state.tables[i]['name']
                table2 = st.session_state.tables[i+1]['name']
                
                st.write(f"Join antara {table1} dan {table2}")
                col1 = st.selectbox(
                    f"Kolom dari {table1}",
                    st.session_state.tables[i]['columns'],
                    key=f"join_col1_{i}"
                )
                col2 = st.selectbox(
                    f"Kolom dari {table2}",
                    st.session_state.tables[i+1]['columns'],
                    key=f"join_col2_{i}"
                )
                join_type = st.selectbox(
                    f"Jenis Join",
                    ["INNER JOIN", "LEFT JOIN", "RIGHT JOIN", "FULL JOIN"],
                    key=f"join_type_{i}"
                )
                join_entries.append({
                    "type": join_type,
                    "condition": f"{table1}.{col1} = {table2}.{col2}"
                })
            
            if st.button("Submit Join Options"):
                st.session_state.joins = join_entries
                st.session_state.step = 3
                st.rerun()

    def show_query_options(self):
        if st.session_state.step == 3:
            st.subheader("Query Options")
            tab_select, tab_where, tab_group, tab_order = st.tabs(["SELECT", "WHERE", "GROUP BY/HAVING", "ORDER BY"])

            with tab_select:
                st.session_state.distinct = st.checkbox("DISTINCT")
                select_vars = {}
                
                # AgGrid untuk pemilihan kolom
                columns_data = []
                for table in st.session_state.tables:
                    for col in table['columns']:
                        columns_data.append({
                            "Tabel": table['name'],
                            "Kolom": col,
                            "Pilih": False,
                            "Agregasi": "None",
                            "Alias": ""
                        })
                
                columns_df = pd.DataFrame(columns_data)
                
                gb = GridOptionsBuilder.from_dataframe(columns_df)
                gb.configure_selection(selection_mode="multiple", use_checkbox=True)
                gb.configure_column("Pilih", headerCheckboxSelection=True)
                gb.configure_column("Agregasi", editable=True, cellEditor='agSelectCellEditor', 
                                  cellEditorParams={'values': ['None', 'SUM', 'COUNT', 'AVG', 'MIN', 'MAX']})
                grid_options = gb.build()
                
                grid_response = AgGrid(
                    columns_df,
                    gridOptions=grid_options,
                    update_mode=GridUpdateMode.SELECTION_CHANGED,
                    fit_columns_on_grid_load=True,
                    height=300,
                    key='columns_grid'
                )
                
                selected_rows = grid_response['selected_rows']
                for row in selected_rows:
                    full_name = f"{row['Tabel']}.{row['Kolom']}"
                    if row['Agregasi'] != "None":
                        full_name = f"{row['Agregasi']}({full_name})"
                    if row['Alias']:
                        full_name += f" AS {row['Alias']}"
                    select_vars[full_name] = True
                st.session_state.select_columns = select_vars

            with tab_where:
                # ... (sama seperti sebelumnya)

            with tab_group:
                # ... (sama seperti sebelumnya)

            with tab_order:
                # ... (sama seperti sebelumnya)

            if st.button("Generate SQL"):
                self.generate_sql()

    # ... (fungsi lainnya tetap sama)

def app():
    app_instance = SQLSimulatorStreamlit()
    
    if st.session_state.step == 0:
        app_instance.initialize_table_input()
    elif st.session_state.step == 1:
        app_instance.show_table_details()
    elif st.session_state.step == 2:
        app_instance.show_join_options()
    elif st.session_state.step == 3:
        app_instance.show_query_options()

if __name__ == "__main__":
    app()

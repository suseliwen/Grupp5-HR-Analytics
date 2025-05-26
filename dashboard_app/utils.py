import duckdb
from pathlib import Path
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st


# A specific class to handle the connection to the DuckDB.
# This class uses a context manager, to make sure  the connection is closed after use.
class DataBase_Connection:
    def __init__(self, db_filename="jobads_data_warehouse.duckdb", read_only=True):
        self.db_path = Path(__file__).parent.parent / db_filename
        self.read_only = read_only
        self.connection = None

    def __enter__(self):
        self.connection = duckdb.connect(database=self.db_path, read_only=True)
        return self.connection
    
    
    def __exit__(self, exc_type, exc_value, traceback):
        if self.connection:
            self.connection.close()



@st.cache_data(ttl=3600)  #cache data for 1 hour
def load_data(mart_table):
    now = datetime.now(ZoneInfo("Europe/Stockholm")).date()

    try:
        with DataBase_Connection() as conn:
            df = conn.execute("SELECT * FROM mart.mart_occupation_social").fetchdf()
            df["publication_date"] = pd.to_datetime(df["publication_date"], errors="coerce").dt.date
            df["application_deadline"] = pd.to_datetime(df["application_deadline"], errors="coerce").dt.date
            df = df[df["application_deadline"] >= now]
        
        print(f"Datan laddas från {mart_table}!")  #debug print 
        return df

    except Exception as e:
        st.error(f"Fel vid inläsning av data från {mart_table}: {e}")
        return pd.DataFrame()



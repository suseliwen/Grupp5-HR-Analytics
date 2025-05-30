import streamlit as st
from utils import DataBase_Connection
import pandas as pd
import plotly.express as px

def load_it_data():
    try:
        with DataBase_Connection () as conn:
            df = conn.execute("SELECT * FROM mart.mart_it_jobs.sql").fetch_df
        return df
    except Exception as e:
        st.error(f"Fel med importering av data från mart modell: {e}")

def main():
    st.title("Yrken med teknisk inriktning")
    st.markdown("Dashboard for IT job related information")

    df = load_it_data()

if __name__ == "__main__":
    main()
import streamlit as st
from utils import DataBase_Connection
import pandas as pd
import plotly.express as px
def load_data(mart_table):
    try:
        with DataBase_Connection() as conn:
            df = conn.execute(f"SELECT * FROM {mart_table}").fetchdf()
            df["publication_date"] = pd.to_datetime(df["publication_date"], errors="coerce").dt.date
            df["application_deadline"] = pd.to_datetime(df["application_deadline"], errors="coerce").dt.date
        return df

    except Exception as e:
        st.error(f"Fel vid inläsning av data från {mart_table}: {e}")
        return pd.DataFrame()
def show_it_metrics(df):
    #counts the amount of coulumns with "is_open"
    active_jobs = df['is_open'].sum() # if 'is_open' in df.columns else "Okänt"
    #counts the amount of unique strings in the occupation column
    occupation_areas = df['occupation'].nunique() if 'occupation' in df.columns else 0
    #counts the amount of unique strings in the employer column
    num_employers = df['employer_name'].nunique() if 'employer_name' in df.columns else 0
    #counts the amount of ads in database
    total_jobs = len(df)
    #adds column with four value (eight if you count description string)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Totala IT annonser", total_jobs)
    col2.metric("Aktiva IT annonser", active_jobs)
    col3.metric("Ockupationsområden", occupation_areas)
    col4.metric("Arbetsgivare", num_employers)

def main():
    st.title("Yrken med teknisk inriktning")
    st.markdown("Dashboard for IT job related information")
    df = load_data("mart.mart_it_jobs")
    #if "application_deadline" is more or equal than the current time marks the specific ad with "is_open" to signify that its still open
    if 'application_deadline' in df.columns:
            df['is_open'] = df['application_deadline'] >= pd.Timestamp.now().date()
    show_it_metrics(df)

if __name__ == "__main__":
    main()

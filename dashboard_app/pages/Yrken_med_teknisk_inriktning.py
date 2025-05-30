import streamlit as st
from utils import load_data
import pandas as pd
import plotly.express as px
def show_it_metrics(df):
    active_jobs = df['is_open'].sum() if 'is_open' in df.columns else "Okänt"
    occupation_areas = df['occupation'].nunique() if 'occupation' in df.columns else 0
    num_employers = df['employer_name'].nunique() if 'employer_name' in df.columns else 0
    total_jobs = len(df)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Totala IT annonser", total_jobs)
    col2.metric("Aktiva IT annonser", active_jobs)
    col3.metric("Ockupations områden", occupation_areas)
    col4.metric("Arbetsgivare", num_employers)

def main():
    st.title("Yrken med teknisk inriktning")
    st.markdown("Dashboard for IT job related information")
    df = load_data("mart.mart_it_jobs")
    if 'application_deadline' in df.columns:
            df['is_open'] = df['application_deadline'] >= pd.Timestamp.now().date()
    show_it_metrics(df)

if __name__ == "__main__":
    main()
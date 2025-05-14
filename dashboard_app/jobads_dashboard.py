import streamlit as st
import duckdb
import pandas as pd
from pathlib import Path
import altair as alt
import plotly.express as px
from utils import DataBase_Connection


# Set up the streamlit page configuration
st.set_page_config(page_title="HR Analytics Dashboard", layout="wide")
st.title("HR Analytics Dashboard")

# Conncetion between occupation field and marts
occupation_to_mart = {
    "Yrken med social inriktning": "marts.marts_occupation_social",
    "Yrken med teknisk inriktning": "marts.marts_it_jobs",
    "Chefer och verksamhetsledare" : "marts.marts_leadership_jobs"
}

# User input for occupation field
st.sidebar.header("Välj yrkesområde")
occupation_field_choice = st.sidebar.selectbox("Välj ett yrkesområde...", list(occupation_to_mart.keys()))

# Get the corresponding mart name from dictionary
mart_table = occupation_to_mart[occupation_field_choice] 

#Open data with context manager
with DataBase_Connection() as conn:
    df = conn.execute(f"SELECT * FROM {mart_table}").fetchdf()

st.subheader(f"Visar jobbannonser för området {occupation_field_choice}")
st.dataframe(df)

# Display the DataFrame in Streamlit
st.markdown("Här visas data baserat på användarens filtrering i sidomenyn.")

# Create a sidebar for user input
st.sidebar.header("Filtrera ditt urval")

# Add a selectbox for region selection
region = df['workplace_region'].dropna().unique()
choice_region = st.sidebar.selectbox("Välj kommun:", sorted(region))

# Add a selectbox for job occupation group selection
occupation = df['occupation_group'].dropna().unique()
choice_occupation = st.sidebar._selectbox("Välj yrkesområde:", sorted(occupation))

# Add a selectbox for employment type selection
employment_type = df['employment_type'].dropna().unique()
choice_employment_type = st.sidebar.selectbox("Välj anställningsform:", sorted(employment_type))


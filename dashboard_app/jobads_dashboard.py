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

#Open data with context manager
with DataBase_Connection() as conn:
    df = conn.execute("SELECT * FROM marts.marts_occupation_social").fetchdf()
    print(df)

# Display the DataFrame in Streamlit
st.subheader("Visar jobbannonser för området yrken med social inriktning")
st.dataframe(df)
st.markdown("Här visas data baserat på användarens filtrering i sidomenyn.")

# Create a sidebar for user input
st.sidebar.header("Filtrera ditt urval:")

# Add a selectbox for region selection
region = df['workplace_region'].dropna().unique()
choice_region = st.sidebar.selectbox("Välj kommun:", sorted(region))

# Add a selectbox for job occupation group selection
occupation = df['occupation_group'].dropna().unique()
choice_occupation = st.sidebar._selectbox("Välj yrkesområde:", sorted(occupation))

# Add a selectbox for employment type selection
employment_type = df['employment_type'].dropna().unique()
choice_employment_type = st.sidebar.selectbox("Välj anställningsform:", sorted(employment_type))


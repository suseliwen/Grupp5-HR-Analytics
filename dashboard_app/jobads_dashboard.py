import streamlit as st
import duckdb
import pandas as pd
from pathlib import Path
import altair as alt
import plotly.express as px
from utils import DataBase_Connection



# ======= PAGE SETUP ========


# Set up the streamlit page configuration
st.set_page_config(page_title="HR Analytics Dashboard", layout="wide")
st.title("HR Analytics Dashboard")

# Conncetion between occupation field and marts
occupation_to_mart = {
    "Alla": "mart.mart_all_jobs",
    "Yrken med social inriktning": "mart.mart_occupation_social",
    "Yrken med teknisk inriktning": "mart.mart_it_jobs",
    "Chefer och verksamhetsledare" : "mart.mart_leadership_jobs"
}


# ======== USER INPUT ========

# User input for occupation field
st.sidebar.header("Välj yrkesområde")
select_occupation = st.sidebar.selectbox("Välj ett yrkesområde...", list(occupation_to_mart.keys()))

# Get the corresponding mart name from dictionary
mart_table = occupation_to_mart[select_occupation] 


# ======== DATA LOADING ========


#Open data with context manager
with DataBase_Connection() as conn:
    df = conn.execute(f"SELECT * FROM {mart_table}").fetchdf()


#======== SIDEBAR ========



# Create a sidebar for user input
st.sidebar.header("Filtrera ditt urval")

# Add a selectbox for job occupation group selection
occupation = df['occupation_group'].dropna().unique()
select_occupation_field = st.sidebar._selectbox("Välj yrkestitel:", ["Alla"] + sorted(occupation.tolist()))

# Add a selectbox for region selection
region = df['workplace_region'].dropna().unique()
select_region = st.sidebar.selectbox("Välj kommun:", ["Alla"] + sorted(region.tolist()))

# Add a selectbox for employment type selection
employment_type = df['employment_type'].dropna().unique()
select_employment_type = st.sidebar.selectbox("Välj anställningsform:", ["Alla"] + sorted(employment_type.tolist()))

st.sidebar.checkbox("Körkort krävs", value=False, key="driving_license_required,")
st.sidebar.checkbox("Egen bil krävs", value=False, key="own_car_required")

#========== DATAFRAME FILTERING ==========

# Filter the dataframe based on user input

filtered_df = df.copy()

if select_region != "Alla":
    filtered_df = filtered_df[filtered_df['workplace_region'] == select_region]

if select_occupation_field != "Alla":
    filtered_df = filtered_df[filtered_df['occupation_group'] == select_occupation_field]

if select_employment_type != "Alla":
    filtered_df = filtered_df[filtered_df['employment_type'] == select_employment_type]



# ========= SHOWING DATA ==========

st.subheader(f"Visar jobbannonser för området {select_occupation}")
st.dataframe(filtered_df)
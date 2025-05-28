import streamlit as st
import duckdb
import pandas as pd
from pathlib import Path
import altair as alt
import plotly.express as px
from utils import DataBase_Connection
from map.hr_map import create_hr_map


# ======= PAGE SETUP ========

# Set up the streamlit page configuration
st.set_page_config(page_title="HR Analytics Dashboard", layout="wide")
st.title("HR Analytics Dashboard")


# Conncetion between occupation field and marts
occupation_to_mart = {

    "Samtliga yrkesområden": "mart.mart_all_jobs",
    "Yrken med social inriktning": "mart.mart_occupation_social",
    "Yrken med teknisk inriktning": "mart.mart_it_jobs",
    "Chefer och verksamhetsledare" : "mart.mart_leadership_jobs"
}

# ======== USER INPUT ========

# User input for occupation field

select_occupation_field = st.sidebar.selectbox("Välj yrkesområde...", list(occupation_to_mart.keys()))

# Get the corresponding mart name from dictionary
mart_table = occupation_to_mart[select_occupation_field] 



# ======== DATA LOADING ========

#Open data with context manager
with DataBase_Connection() as conn:
    df = conn.execute(f"SELECT * FROM {mart_table}").fetchdf()


#======== SIDEBAR ========


# Create a sidebar for user input
st.sidebar.header("Filtrera ditt urval")

# Add a selectbox for job occupation group selection
occupation = df['occupation'].dropna().unique()
select_occupation = st.sidebar.selectbox("Välj yrkestitel:", ["Alla"] + sorted(occupation.tolist()))

# Add a selectbox for region selection
region = df['workplace_region'].dropna().unique()
select_region = st.sidebar.selectbox("Välj län:", ["Alla"] + sorted(region.tolist()))

# Add a selectbox for employment type selection
employment_type = df['employment_type'].dropna().unique()
select_employment_type = st.sidebar.selectbox("Välj anställningsform:", ["Alla"] + sorted(employment_type.tolist()))

st.sidebar.checkbox("Körkort krävs", value=False, key="driving_license_required")
st.sidebar.checkbox("Egen bil krävs", value=False, key="own_car_required")
st.sidebar.checkbox("Erfarenhet krävs", value=False, key="experience_required")


#========== DATAFRAME FILTERING ==========

# Filter the dataframe based on user input

filtered_df = df.copy()

if select_region != "Alla":
    filtered_df = filtered_df[filtered_df['workplace_region'] == select_region]

if select_occupation != "Alla":
    filtered_df = filtered_df[filtered_df['occupation'] == select_occupation]

if select_employment_type != "Alla":
    filtered_df = filtered_df[filtered_df['employment_type'] == select_employment_type]

if st.session_state.get("driving_license_required"):
    filtered_df = filtered_df[filtered_df['driving_license_required'] == True]

if st.session_state.get("own_car_required"):
    filtered_df = filtered_df[filtered_df['own_car_required'] == True]

if st.session_state.get("experience_required"):
    filtered_df = filtered_df[filtered_df['experience_required'] == True]




# ========= SHOWING DATA ==========

st.subheader(f"Visar jobbannonser för {select_occupation_field}")

col1, col2, col3 = st.columns(3)

# === Column 1 - Topp 5 occupation ===
with col1:
    st.markdown("<h4 style='font-size:18px; margin-bottom:10px;'>Topp 5 mest efterfrågade yrkestitlar</h4>", unsafe_allow_html=True)
    job_title_counts = (
        filtered_df['occupation']
        .value_counts()
        .head(5)
        .reset_index()
    )
    job_title_counts.columns = ['occupation', 'count'] 
    fig1 = px.bar(
        job_title_counts,
        x='occupation',
        y='count',
        title='Antal annonser per yrkestitel',
        text='count',
        labels={'occupation': 'Yrkestitel', 'count': 'Antal'}
    )
    fig1.update_traces(textposition='inside')
    fig1.update_layout(xaxis_tickangle=-30)
    st.plotly_chart(fig1, use_container_width=True)

# === Column 2 - Top 5 regions ===
with col2:
    st.markdown("<h4 style='font-size:18px; margin-bottom:10px;'>Topp 5 län med lediga jobb</h4>", unsafe_allow_html=True)
    region_filtered_df = filtered_df[filtered_df['workplace_region'] != 'Ingen data']
    region_counts = (
        filtered_df['workplace_region']
        .value_counts()
        .head(5)
        .reset_index()
    )
    region_counts.columns = ['workplace_region', 'count']
    fig2 = px.bar(
        region_counts,
        x='workplace_region',
        y='count',
        title='Antal annonser per län',
        text='count',
        labels={'workplace_region': 'Län', 'count': 'Antal'}
    )
    fig2.update_traces(textposition='inside')
    fig2.update_layout(xaxis_tickangle=-30)
    st.plotly_chart(fig2, use_container_width=True)

# === Column 3 - Contains the map ===
with col3:

    create_hr_map(filtered_df, select_occupation_field)
   

st.dataframe(filtered_df)
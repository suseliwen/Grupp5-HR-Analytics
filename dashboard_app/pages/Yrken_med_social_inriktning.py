import streamlit as st
from utils import DataBase_Connection
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

# ======= PAGE SETUP ========

st.set_page_config(page_title="HR Analytics Dashboard", layout="wide")
st.title("Yrkesområden med social inriktning")

st.markdown("Visar tillgängliga arbeten inom yrkesområden med social inriktning. ")
st.sidebar.success("Viktig info")

progress_bar = st.sidebar.progress(0)
status_text = st.sidebar.empty()

# ======== DATA LOADING ========


# with DataBase_Connection() as conn:
#      df_top10 = conn.execute("SELECT * FROM mart_top_ten_social_occ").fetchdf()
    
with DataBase_Connection() as conn:
    df = conn.execute("SELECT * FROM mart.mart_all_jobs").fetchdf()
    df = df[df["occupation_field"] == "Yrken med social inriktning"]
     

# ======== SHOW DATA ========
column1, column2, column3, column4 = st.columns(4)

column1.metric("Antal jobbannonser", df.shape[0])
column2.metric("Antal unika yrkestitlar", df['occupation'].nunique())
column3.metric("Antal unika arbetsgivare", df['employer_name'].nunique())
column4.metric("Antal unika kommuner", df['workplace_region'].nunique())

column4, column5 = st.columns(2)

# ======== Pagination Logic ======== INTE EGEN KOD!!!
st.markdown("### Annonser")

rows_per_page = 50  # Visa 50 rader per sida
total_rows = len(df)
total_pages = (total_rows - 1) // rows_per_page + 1

# Välj sida i en selectbox eller number_input
page = st.number_input("Sida", min_value=1, max_value=total_pages, value=1, step=1)

start_idx = (page - 1) * rows_per_page
end_idx = min(start_idx + rows_per_page, total_rows)

st.markdown(f"Visar rader **{start_idx + 1}–{end_idx}** av totalt **{total_rows}**.")

# Visa bara den aktuella sidan
st.dataframe(df.iloc[start_idx:end_idx], use_container_width=True)
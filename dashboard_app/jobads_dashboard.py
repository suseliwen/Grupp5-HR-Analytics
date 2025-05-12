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
    df = conn.execute("SELECT * FROM refined.fct_job_ads LIMIT 10").fetchdf()
    print(df)


# Display the DataFrame in Streamlit
st.subheader("Visar jobbannonser för området yrken med social inriktning")
st.dataframe(df)
st.markdown("Här visas data hämtat från duckdb.")



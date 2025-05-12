import streamlit as st
import duckdb
import pandas as pd
from pathlib import Path


# Set up the page configuration
st.set_page_config(page_title="HR Analytics Dashboard", layout="wide")
st.title("HR Analytics Dashboard")


# Connect to DuckDB to get data from the data warehouse
conn = duckdb.connect(database="../jobads_data_warehouse.duckdb", read_only=True)

query = "SELECT * FROM marts.marts_occupation_social LIMIT 10"
df = conn.execute(query).fetchdf()

# Close the connection
conn.close()

# Display the DataFrame in Streamlit
st.subheader("Visar jobbannonser för området yrken med social inriktning")
st.dataframe(df)
st.markdown("Här visas data hämtat från duckdb.")


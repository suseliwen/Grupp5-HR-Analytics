import streamlit as st
from utils import DataBase_Connection
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo #Necessary for timezone conversion

# ======= PAGE SETUP ========

now = datetime.now(ZoneInfo("Europe/Stockholm"))

st.set_page_config(page_title="HR Analytics Dashboard", layout="wide")
st.title("Yrkesområden med social inriktning")

#st.success("Annonserna hämtas från Arbetsförmedlingen och uppdateras varje natt.")


# ======== DATA LOADING ========


# with DataBase_Connection() as conn:
#       df_top10 = conn.execute("SELECT * FROM mart_top_ten_social_occ").fetchdf()
    
with DataBase_Connection() as conn:
    df = conn.execute("SELECT * FROM mart.mart_all_jobs").fetchdf()
    df = df[df["occupation_field"] == "Yrken med social inriktning"]
    
    df["publication_date"] = pd.to_datetime(df["publication_date"], errors="coerce")
    df["application_deadline"] = pd.to_datetime(df["application_deadline"], errors="coerce") 
    df = df[df["application_deadline"] >= now]


# with DataBase_Connection() as conn:
#     df_top10 = conn.execute("SELECT * FROM mart_top_ten_social_occ").fetchdf()
#     df_top10 = df_top10[df_top10["occupation_field"] == "Yrken med social inriktning"] 
#     df["publication_date"] = pd.to_datetime(df["publication_date"], errors="coerce") 

with DataBase_Connection() as conn:
    df_trending_ads = conn.execute("SELECT * FROM mart.mart_all_jobs").fetchdf()  
    df_trending_ads = df_trending_ads[df_trending_ads["occupation_field"] == "Yrken med social inriktning"]
    df["publication_date"] = pd.to_datetime(df["publication_date"], errors="coerce")


# ======== SIDEBAR ========
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
select_employment_type = st.sidebar.selectbox("Välj anställningstyp:", ["Alla"] + sorted(employment_type.tolist()))
# Add a selectbox for employer name selection
duration = df['duration'].dropna().unique()
select_duration = st.sidebar.selectbox("Välj anställningens längd:", ["Alla"] + sorted(duration.tolist()))

st.sidebar.checkbox("Körkort krävs", value=False, key="driving_license_required")
st.sidebar.checkbox("Egen bil krävs", value=False, key="own_car_required")
st.sidebar.checkbox("Erfarenhet krävs", value=False, key="experience_required")

# ======== DATAFRAME FILTERING ==========
# Filter the DataFrame based on user input
filtered_df = df.copy()
if select_occupation != "Alla":
    filtered_df = filtered_df[filtered_df["occupation"] == select_occupation]
if select_region != "Alla":
    filtered_df = filtered_df[filtered_df["workplace_region"] == select_region]
if select_employment_type != "Alla":
    filtered_df = filtered_df[filtered_df["employment_type"] == select_employment_type]
if select_duration != "Alla":
    filtered_df = filtered_df[filtered_df["duration"] == select_duration]
if st.session_state.get("driving_license_required"):
    filtered_df = filtered_df[filtered_df["driving_license_required"] == True]
if st.session_state.get("own_car_required"):
    filtered_df = filtered_df[filtered_df["own_car_required"] == True]
if st.session_state.get("experience_required"):
    filtered_df = filtered_df[filtered_df["experience_required"] == True]


# ======== SHOW DATA ========
# Remove rows with 'Ingen data' in 'workplace_region' column
unique_regions = df[df['workplace_region'] != 'Ingen data']['workplace_region'].nunique()

column1, column2, column3, column4 = st.columns(4)

column1.metric("Antal jobbannonser", df.shape[0])
column2.metric("Antal unika yrkestitlar", df['occupation'].nunique())
column3.metric("Antal unika arbetsgivare", df['employer_name'].nunique())
column4.metric("Antal län", unique_regions)


column4, column5 = st.columns(2)

with column4:    
    cutoff_date = datetime.today() - timedelta(days=30)
    df_trending_ads = df_trending_ads[df_trending_ads["publication_date"] >= cutoff_date]

    trend_df = (
        df_trending_ads.groupby(df_trending_ads["publication_date"].dt.date)
        .size()
        .reset_index(name="count")
        .sort_values(by="publication_date")
    )
    fig = px.line(
        trend_df,
        x="publication_date",
        y="count",
        title="Antal annonser publicerade de senaste 30 dagarna",
        labels={"publication_date": "Datum", "count": "Antal annonser"},
    )
    st.plotly_chart(fig, use_container_width=True)

with column5:    
    employment_type_counts = df["employment_type"].value_counts()
    fig = px.pie(
        employment_type_counts,
        values=employment_type_counts.values,
        names=employment_type_counts.index,
        title="Fördelning av annonser per anställningstyp",
        labels={"value": "Anställningstyp", "name": "Antal annonser"},
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
   
  


# ======== PAGINATION ======== 
st.markdown("#### Annonser utifrån dina val")

rows_per_page = 100 
total_rows = len(df)
total_pages = (total_rows - 1) // rows_per_page + 1 


page = st.number_input("Sida", min_value=1, max_value=total_pages, value=1, step=1)

start_idx = (page - 1) * rows_per_page
end_idx = min(start_idx + rows_per_page, total_rows)
current_page_df = filtered_df.iloc[start_idx:end_idx]
st.markdown(f"Visar {len(current_page_df)} rader (av {len(filtered_df)} matchande annonser)")



st.dataframe(current_page_df, use_container_width=True)

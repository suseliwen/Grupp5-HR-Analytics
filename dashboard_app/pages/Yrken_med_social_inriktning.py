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

st.markdown("Visar tillgängliga arbeten inom yrkesområden med social inriktning. ")
st.sidebar.success("Viktig info")

progress_bar = st.sidebar.progress(0)
status_text = st.sidebar.empty()

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
     

# ======== SHOW DATA ========
column1, column2, column3, column4 = st.columns(4)

column1.metric("Antal jobbannonser", df.shape[0])
column2.metric("Antal unika yrkestitlar", df['occupation'].nunique())
column3.metric("Antal unika arbetsgivare", df['employer_name'].nunique())
column4.metric("Antal unika regioner", df['workplace_region'].nunique())

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
   

    
column6, column7 = st.columns(2)
with column6:
    st.markdown("<h4 style='font-size:18px; margin-bottom:10px;'>Topp 5 mest efterfrågade yrkestitlar</h4>", unsafe_allow_html=True)
    job_title_counts = (
        df['occupation']
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
        text='count'
    )
    fig1.update_traces(textposition='inside')
    fig1.update_layout(xaxis_tickangle=-30)
    st.plotly_chart(fig1, use_container_width=True)


# ======== Pagination Logic ======== INTE EGEN KOD!!!
st.markdown("### Annonser")

rows_per_page = 100  # Visa 50 rader per sida
total_rows = len(df)
total_pages = (total_rows - 1) // rows_per_page + 1

# Välj sida i en selectbox eller number_input
page = st.number_input("Sida", min_value=1, max_value=total_pages, value=1, step=1)

start_idx = (page - 1) * rows_per_page
end_idx = min(start_idx + rows_per_page, total_rows)

st.markdown(f"Visar rader **{start_idx + 1}–{end_idx}** av totalt **{total_rows}**.")


# Visa bara den aktuella sidan
st.dataframe(df.iloc[start_idx:end_idx], use_container_width=True)
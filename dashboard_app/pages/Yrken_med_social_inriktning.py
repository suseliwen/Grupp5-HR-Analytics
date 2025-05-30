import streamlit as st
from utils import load_data
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from datetime import datetime, date, timedelta
from zoneinfo import ZoneInfo #Necessary for timezone conversion
import logging

# ======= LOGGING SETUP ========
logging.basicConfig(
    filename ='app.log',
    level=logging.ERROR, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
# ======= PAGE SETUP ========

now = datetime.now(ZoneInfo("Europe/Stockholm")).date()

#st.success("Annonserna hämtas från Arbetsförmedlingen och uppdateras varje natt.") #If I manage to use a dagster pipeline

   
# ======= ERROR HANDLING ========
def check_if_dataframe_empty(df, messsage):
    if df.empty:
        logging.warning(messsage)
        st.warning(messsage)
        return True
    return False

# ======= RESET SIDEBAR FILTERS FUNCTION ========
def reset_sidebar_filters():
    st.session_state["occupation_group"] = "Alla"
    st.session_state["occupation"] = "Alla"
    st.session_state["region"] = "Alla"
    st.session_state["employment_type"] = "Alla"
    st.session_state["driving_license_required"] = False
    st.session_state["own_car_required"] = False
    st.session_state["experience_required"] = False
    st.rerun()

# ======== DISPLAY SIDEBAR FUNCTION ========
def display_sidebar(df):
    st.sidebar.header("Filtrera ditt urval")    

    if st.sidebar.button("Rensa filter", key="reset_filters"):
        reset_sidebar_filters()
    
    # Add a selectbox for job occupation_group selection
    occupation_group = df['occupation_group'].dropna().unique()
    selected_occupation_group = st.sidebar.selectbox(
        "Välj yrkesområde:", 
        ["Alla"] + sorted(occupation_group.tolist()),
        key="occupation_group"
    )
    
    # Add a selection for job occupation selection, and filter the DataFrame based on the selected occupation_group
    if selected_occupation_group != "Alla":
        df_filtered_by_group = df[df["occupation_group"] == selected_occupation_group]
    else:
        df_filtered_by_group = df     
    
    occupation = df_filtered_by_group['occupation'].dropna().unique()
    selected_occupation = st.sidebar.selectbox(
        "Välj yrke:", 
        ["Alla"] + sorted(occupation.tolist()),
        key="occupation"
    ) 

    if selected_occupation != "Alla":
        df_filtered_by_group = df_filtered_by_group[df_filtered_by_group["occupation"] == selected_occupation]


    # Add a selectbox for region selection, filtered by the selection above
    region = df_filtered_by_group['workplace_region'].dropna().unique()
    selected_region = st.sidebar.selectbox(
        "Välj län:", 
        ["Alla"] + sorted(region.tolist()),
        key="region"
    )

    # Add a selectbox for employment type selection
    employment_type = df_filtered_by_group['employment_type'].dropna().unique()
    selected_employment_type = st.sidebar.selectbox(
        "Välj anställningsform:", 
        ["Alla"] + sorted(employment_type.tolist()),
        key="employment_type"
    )

    # Add checkboxes for aux-attributes
    require_driving_license = st.sidebar.checkbox("Körkort krävs", value=False, key="driving_license_required")
    require_own_car = st.sidebar.checkbox("Egen bil krävs", value=False, key="own_car_required")
    require_experience = st.sidebar.checkbox("Erfarenhet krävs", value=False, key="experience_required")

  

    filters = {
        "occupation_group": selected_occupation_group,
        "occupation": selected_occupation,
        "region": selected_region,
        "employment_type": selected_employment_type,
        "driving_license_required": require_driving_license,
        "own_car_required": require_own_car,
        "experience_required": require_experience
    }
    return filters
     
def apply_sidebar_filters(df, filters):
    filtered_df = df.copy()

    if filters["occupation_group"] != "Alla":
        filtered_df = filtered_df[filtered_df["occupation_group"] == filters["occupation_group"]]
    if filters["occupation"] != "Alla":
        filtered_df = filtered_df[filtered_df["occupation"] == filters["occupation"]]
    if filters["region"] != "Alla":
        filtered_df = filtered_df[filtered_df["workplace_region"] == filters["region"]]
    if filters["employment_type"] != "Alla":
        filtered_df = filtered_df[filtered_df["employment_type"] == filters["employment_type"]]
    if filters["driving_license_required"]:
        filtered_df = filtered_df[filtered_df["driving_license_required"] == True]
    if filters["own_car_required"]:
        filtered_df = filtered_df[filtered_df["own_car_required"] == True]
    if filters["experience_required"]:
        filtered_df = filtered_df[filtered_df["experience_required"] == True]

    return filtered_df

# ======= DISPLAY DATAFRAME FUNCTION ========
def create_display_df(filtered_df):    
    
    # Define the columns to display
    columns_to_show = {
        "publication_date": "Publiceringsdatum",
        "headline": "Rubrik",
        "employer_name": "Arbetsgivare",
        "occupation": "Yrkestitel",
        "occupation_group": "Yrkesområde",
        "workplace_region": "Län",
        "application_deadline": "Sista ansökningsdag",
        "application_url": "Annons",
    }
    
    # Create a new DataFrame with the selected columns
    display_df = (
        filtered_df
        .sort_values("publication_date", ascending=False)
        [list(columns_to_show.keys())]
        .rename(columns=columns_to_show)               
    )
    return display_df

# ======== SHOW METRIC DATA FUNCTION ========
def show_metric_data(df):
    st.markdown("#### Sammanfattning av annonser utifrån dina val")
    
    column1, column2, column3 = st.columns(3)     
    column4, column5, column6 = st.columns(3)

    with column1:
        df["week"] = df["publication_date"].apply(lambda d: d.isocalendar().week if pd.notnull(d) else None)
        weekly_counts = (
            df.groupby("week")
            .size()
            .reset_index(name="count")
            .sort_values("week")
        )    
        if len(weekly_counts) >= 2:
                latest = weekly_counts.iloc[-1]
                previous = weekly_counts.iloc[-2]
                st.metric(
                    label=f"Annonser vecka {int(latest['week'])}",
                    value=int(latest['count']),
                    delta=int(latest['count']) - int(previous['count'])
                )
        elif len(weekly_counts) == 1:
            latest = weekly_counts.iloc[-1]
            st.metric(
                label=f"Annonser vecka {int(latest['week'])}",
                value=int(latest['count']),
                delta="Ingen föregående vecka"
            )
        else:
            st.metric("Annonser per vecka", "Inga data")
    
    with column2:
        st.metric("Antal unika yrken", df['occupation'].nunique()) 
    
    with column3:
        st.metric("Antal unika arbetsgivare", df['employer_name'].nunique())
    
    with column4:
        st.metric("Antal annonser", df.shape[0])
        with st.popover("Visa antal annonser per vecka"):
            st.markdown("Antal annonser de senaste veckorna")
            
            weeks = weekly_counts["week"].astype(str).apply(lambda w: f"v{w}")
            counts = weekly_counts["count"]
        
            fig = px.bar(
                x=weeks, 
                y=counts, 
                labels={"x": "Vecka", "y": "Antal annonser"},
                color=counts,
                color_continuous_scale=["#00441b", "#006d2c", "#238b45", "#41ae76", "#66c2a4", "#99d8c9"],
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)       
    
    with column5:
        st.metric("Det mest eftersökta yrket", df['occupation'].value_counts().idxmax())
        with st.popover("Visa topp 5 yrken"):
            st.markdown("Topp 5 yrken")
            
            counts = df['occupation'].value_counts().nlargest(5)

            fig = px.bar(
                x=counts.index, 
                y=counts.values, 
                labels={"x": "Yrke", "y": "Antal annonser"},
                color=counts,
                color_continuous_scale=["#00441b", "#006d2c", "#238b45", "#41ae76", "#66c2a4", "#99d8c9"],
            )
            fig.update_layout(xaxis_tickangle=-45) 
            st.plotly_chart(fig, use_container_width=True)      
    
    with column6:
        st.metric("Den arbetsgivare som annonserat mest", df['employer_name'].value_counts().idxmax())
        with st.popover("Visa topp 5 arbetsgivare"):
            st.markdown("Topp 5 arbetsgivare")
            
            counts = df['employer_name'].value_counts().nlargest(5)

            fig = px.bar(
                x=counts.index, 
                y=counts.values, 
                labels={"x": "Arbetsgivare", "y": "Antal annonser"}, 
                color=counts,
                color_continuous_scale=["#00441b", "#006d2c", "#238b45", "#41ae76", "#66c2a4", "#99d8c9"],
            )
            fig.update_layout(xaxis_tickangle=-60)
            st.plotly_chart(fig, use_container_width=True)     

# ======== PLOTTING FUNCTIONS ========
def employment_type_distribution(df):
    if df.empty or df["employment_type"].dropna().empty:
        st.info("Inga annonser matchar dina val.")
        return
    st.markdown("#### Fördelning av annonser utifrån anställningstyp")

    employment_type_counts = df["employment_type"].value_counts()

    # Colors for the charts
    custom_greens = px.colors.sequential.Greens[2:5]  # ['#00441b', '#006d2c', '#238b45', "#41ae76", "#66c2a4", "#99d8c9"]  

    fig = px.pie(
            employment_type_counts,
            values=employment_type_counts.values,
            names=employment_type_counts.index,
            title="Fördelning av annonser per anställningstyp",
            #labels={"value": "Anställningstyp", "name": "Antal annonser"},
            color_discrete_sequence=["#00441b", "#006d2c", "#238b45", "#41ae76", "#66c2a4", "#99d8c9"],
            hole=0.4,
        )
    #fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

def ads_per_week(df):
    if df.empty or df["publication_date"].dropna().empty:
        st.info("Inga annonser matchar dina val.")
        return
    st.markdown("#### Antal annonser publicerade per vecka")

    df["week"] = df["publication_date"].apply(lambda d: d.isocalendar().week if pd.notnull(d) else None)


    weekly_counts = (
        df.groupby("week")
        .size()
        .reset_index(name="count")
        .sort_values(by="week")
    )
    fig = px.bar(
        weekly_counts,
        x="week",
        y="count",
        title="Antal annonser publicerade per vecka",
        labels={"week": "Vecka", "count": "Antal annonser"},
        color_continuous_scale=["#00441b", "#006d2c", "#238b45", "#41ae76", "#66c2a4", "#99d8c9"],
        color="count",
        color_discrete_sequence=px.colors.qualitative.Plotly,
    )                               
    st.plotly_chart(fig, use_container_width=True)

# ======== PAGINATION FUNCTION ======== 
def pagination(df):
    st.markdown("#### Annonser utifrån dina val, sorterat efter publiceringsdatum")

    rows_per_page = 100 
    total_rows = len(df)
    total_pages = (total_rows - 1) // rows_per_page + 1 


    page = st.number_input("Sida", min_value=0, max_value=total_pages, value=1, step=1)

    start_idx = (page - 1) * rows_per_page
    end_idx = min(start_idx + rows_per_page, total_rows)
    current_page_df = df.iloc[start_idx:end_idx]
    st.markdown(f"Visar {len(current_page_df)} rader (av {len(df)} matchande annonser)")
    return current_page_df

# ======== MAIN FUNCTION ========

def main():
    
    st.set_page_config(page_title="HR Analytics Dashboard", layout="wide")
    st.title("Yrkesområden med social inriktning")
    st.progress(0.1)  # Show a progress bar while loading data
    st.markdown("---")
    
  

    # Load the data
    df = load_data("mart.mart_occupation_social")
    filters = display_sidebar(df)
    filtered_df = apply_sidebar_filters(df, filters)

    if check_if_dataframe_empty(df, "Inga efter inläsning från databasen."):       
        return
    if check_if_dataframe_empty(filtered_df, "Inga annonser matchar din filtrering. Försök igen!"):
        return
    
    display_df = create_display_df(filtered_df)


    show_metric_data(filtered_df)
    st.markdown("---")

    column1, column2 = st.columns(2)
   
    with column1:
        employment_type_distribution(filtered_df)
    
    with column2:
        ads_per_week(filtered_df)
  
    # Display the data - without the HTML table    
    current_page_df = pagination(display_df)
    st.dataframe(current_page_df, use_container_width=True)
   
   
    # # Display the pagination - with the HTML table
    # current_page_df = pagination(display_df)
    # st.markdown(current_page_df.to_html(escape=False, index=False), unsafe_allow_html=True)
 

if __name__ == "__main__":
    main()
   
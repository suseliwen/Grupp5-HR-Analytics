import streamlit as st
from utils import load_data
from utils import get_latest_ingestion
from utils import gemini_chat
import google.generativeai as genai
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns
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
    st.session_state["expiring_ads"] = False
    st.rerun()

# ======== DISPLAY SIDEBAR FUNCTION ========
def display_sidebar(df):

    if st.sidebar.button("Rensa filter", key="reset_filters"):
        reset_sidebar_filters()
    
    spacer = st.sidebar.empty()
    spacer.markdown("<hr style='margin: 0.1rem 0;'>", unsafe_allow_html=True)

    # Add toggle to show ads which expires within 3 days
    show_expiring_ads = st.sidebar.toggle(
        "### Se annonser som löper ut inom fem dagar",
        value=False,
        key="expiring_ads"
    )      
     
    st.sidebar.header("Filtrera ditt urval")      
       
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
    require_experience = st.sidebar.checkbox("Ingen erfarenhet krävs", value=False, key="experience_required")

  

    filters = {
        "occupation_group": selected_occupation_group,
        "occupation": selected_occupation,
        "region": selected_region,
        "employment_type": selected_employment_type,
        "driving_license_required": require_driving_license,
        "own_car_required": require_own_car,
        "experience_required": require_experience,
        "expiring_ads": show_expiring_ads
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
        filtered_df = filtered_df[filtered_df["experience_required"] == False]
    if filters.get("expiring_ads", False):
        today = date.today()
        deadline_limit = today + timedelta(days=5)
        filtered_df = filtered_df[
            (pd.to_datetime(filtered_df["application_deadline"]).dt.date >= today) &
            (pd.to_datetime(filtered_df["application_deadline"]).dt.date <= deadline_limit)
        ]       
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
        latest = get_latest_ingestion()
        if latest:
            st.metric("Data senast inläst", latest.strftime("%Y-%m-%d"))
        else:
            st.warning("Kunde inte läsa uppdateringsdatum.")

    with column2:
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
                label=f"Nytillkomna annonser vecka {int(latest['week'])}",
                value=int(latest['count']),
                delta=int(latest['count']) - int(previous['count'])
            )
        elif len(weekly_counts) == 1:
            latest = weekly_counts.iloc[-1]
            st.metric(
                label=f"Nytillkomna annonser vecka {int(latest['week'])}",
                value=int(latest['count']),
                delta="Ingen föregående vecka"
            )
        else:
            st.metric("Nytillkomna annonser", "Inga data")
   

    with column3:
        st.metric("Antal unika arbetsgivare", df['employer_name'].nunique())
    
    with column4:
        st.metric("Antal aktiva annonser", df.shape[0])
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
        st.metric("Det mest eftersökta yrket just nu", df['occupation'].value_counts().idxmax())
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
    employment_type_counts = df["employment_type"].value_counts()
 

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

def heatmap(df):
    df = df.dropna(subset=["occupation_group", "workplace_region"])

    pivot_df = df.pivot_table(
        index = "occupation_group",
        columns = "workplace_region",
        values = "occupation",
        aggfunc = "count", 
        fill_value = 0
    )
    top_occupations = pivot_df.sum(axis = 1).nlargest(10).index
    top_regions = pivot_df.sum(axis = 0).nlargest(10).index

    filtered_pivot_df = pivot_df.loc[top_occupations, top_regions]

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.heatmap(filtered_pivot_df, cmap="Greens", annot=True, fmt="d", ax=ax)
    st.pyplot(fig)
    

    

    

def aux_attributes(df):
    num_driver_license = df["driving_license_required"].sum()
    num_own_car = df["own_car_required"].sum()
    num_experience = df["experience_required"].sum()
    total = len(df)

    aux_data = pd.DataFrame({
        "Krav": ['Körkort', 'Egen bil', 'Erfarenhet'],
        "Antal": [num_driver_license, num_own_car, num_experience], 
        "Andel (%)": [
            f"{100 * num_driver_license / total:.1f}%",
            f"{100 * num_own_car / total:.1f}%",
            f"{100 * num_experience / total:.1f}%"
        ]
    })
    aux_data = aux_data.sort_values("Antal", ascending=True)

    fig = px.bar(
        aux_data, 
        x="Antal", 
        y="Krav", 
        orientation='h', 
        text="Andel (%)", 
        title="Andel annonser där krav finns",
        color="Antal",
        color_continuous_scale=["#00441b", "#238b45", "#66c2a4"],
    )
    
    fig.update_layout(xaxis_title="Antal annonser", yaxis_title="Krav")
    st.plotly_chart(fig, use_container_width=True)

# ======= EXPIRING ADS =========
def show_expiring_ads(filtered_df):
    st.subheader("Annonser som löper ut inom 5 dagar")
        
    st.markdown("Endast annonser som snart stänger visas nedan.")
        
    column1, column2, column3, column4 = st.columns(4)

    with column1:
        st.metric("Antal annonser", len(filtered_df))
    
    with column2:
        df_no_experince = filtered_df[filtered_df['experience_required'] == False]
        num_of_no_experience = len(df_no_experince)
        st.metric("Antal annonser utan krav på erfarenhet", num_of_no_experience)

    with column3:
        st.metric("Yrket med flest annonser", filtered_df["occupation"].value_counts().idxmax())
    
    with column4:
        st.metric("Länet med flest annonser", filtered_df['workplace_region'].value_counts().idxmax())
    
       
    st.markdown("---")

    column6, column7 = st.columns([1,2])

    with column6:
        st.markdown("Kolumn1")
    
    with column7:
        st.markdown("Kolumn 2")
    
    st.markdown("---")

    
    display_df = create_display_df(filtered_df)
    current_page_df = pagination(display_df)
    st.dataframe(current_page_df, use_container_width=True)

# ======= USING LLM TO SPOT TRENDS ==========
def get_weekly_occupation_stats(df):
    df = df.copy()

    df["week"] = pd.to_datetime(df["publication_date"]).dt.isocalendar().week
    weekly_stats = (
        df.groupby(["occupation", "week"])
        .size()
        .reset_index(name = "num_ads")
        .sort_values(["occupation", "week"])
    )
    return weekly_stats

from utils import gemini_chat

def get_weekly_occupation_stats(df):
    df = df.copy()
    df["week"] = pd.to_datetime(df["publication_date"]).dt.isocalendar().week
    weekly_stats = (
        df.groupby(["occupation", "week"])
        .size()
        .reset_index(name="num_ads")
        .sort_values(["occupation", "week"])
    )
    return weekly_stats

def build_prompt(weekly_stats):
    # Steg 1: Hämta den "senaste kompletta veckan" (ex: 21, om 22 är pågående)
    latest_complete_week = weekly_stats["week"].max() - 1

    # Steg 2: Välj de tre veckorna: v19, v20, v21
    relevant_weeks = [latest_complete_week - 2, latest_complete_week - 1, latest_complete_week]
    recent_data = weekly_stats[weekly_stats["week"].isin(relevant_weeks)]

    # Steg 3: Skapa prompt
    prompt = f"""
Här är en sammanställning av antal jobbannonser per yrke under vecka {relevant_weeks[0]}, {relevant_weeks[1]} och {relevant_weeks[2]}:

{recent_data.to_string(index=False)}

Fokusera på att analysera förändringen i antal annonser mellan vecka {relevant_weeks[1]} och vecka {relevant_weeks[2]}. Identifiera gärna något yrke där det syns en tydlig ökning eller minskning. Skriv max två insikter på svenska som kan hjälpa en rekryterare att agera smart.
"""
    return prompt

def show_ai_insight(df):
    st.markdown("#### Rekryterartips från AI")

    if st.button("Fråga AI om trender de senaste veckorna"):
        with st.spinner("Analyserar pågår..."):
            weekly_stats = get_weekly_occupation_stats(df)
            prompt = build_prompt(weekly_stats)
            response = gemini_chat(prompt)
            st.info(response)
    else:
        st.caption("Klicka på knappen för att generera en analys")
    
#def matching_with_ad(df);
    



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
    st.title("Yrken med social inriktning")    
    st.markdown("---")   
  

    # Load the data
    df = load_data("mart.mart_occupation_social")
    filters = display_sidebar(df)
    filtered_df = apply_sidebar_filters(df, filters)

    if check_if_dataframe_empty(df, "Inga efter inläsning från databasen."):       
        return
    if check_if_dataframe_empty(filtered_df, "Inga annonser matchar din filtrering. Försök igen!"):
        return      

    if filters.get("expiring_ads", False):
        show_expiring_ads(filtered_df)        
    
    else:      
    
        tab1, tab2, tab3 = st.tabs(["Översikt 📎", "Heatmap 📎", "Matcha kandidater med jobb 📎"])

        with tab1:
            show_metric_data(filtered_df)
            st.markdown("---")

            column1, column2, column3 = st.columns(3)
    
            with column1:
                employment_type_distribution(filtered_df)            
    
        
            with column2:
                aux_attributes(filtered_df)

            with column3:
                show_ai_insight(filtered_df)    

            st.markdown("---")

        with tab2:
            col1, col2 = st.columns([2, 1])

            with col1:
                heatmap(filtered_df)
            
            with col2:
                st.markdown("""
                ### Vad visar heatmappen?
                            
                Heatmappen visar **antalet jobbannonser** för olika yrkesområden och län under den valda perioden.  
                Ju mörkare färg, desto fler annonser för den kombinationen av yrke och region. 
                            
                ---

                - Identifiera **var det är störst rekryteringsbehov**  
                            
                - Se **vilka län som har flest annonser** inom olika yrken  
                            
                Använd datan för att prioritera **rekryteringsinsatser**  

                ---            
                                            
                Endast **topp 10 yrken/län** visas för tydlighet  
                            
                        
                        """)               

    
        # Display the data - without the HTML table
        display_df = create_display_df(filtered_df)    
        current_page_df = pagination(display_df)
        st.dataframe(current_page_df, use_container_width=True)   
    
    
        # # Display the pagination - with the HTML table
        # current_page_df = pagination(display_df)
        # st.markdown(current_page_df.to_html(escape=False, index=False), unsafe_allow_html=True)
    

if __name__ == "__main__":
    main()
    
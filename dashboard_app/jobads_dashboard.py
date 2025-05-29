import streamlit as st
import plotly.express as px
from utils import load_data
from utils import get_latest_ingestion
from map.hr_map import create_hr_map

# ======= RESET SIDEBAR FILTERS FUNCTION ========
def reset_sidebar_filters():
    st.session_state["occupation_field"] = "Alla"
    st.session_state["selected_occupation_group"] = "Alla"
    st.session_state["occupation"] = "Alla"
    st.session_state["region"] = "Alla"
    st.session_state["employment_type"] = "Alla"
    st.session_state["driving_license_required"] = False
    st.session_state["own_car_required"] = False
    st.session_state["experience_required"] = False
    st.rerun()

# ======== SIDEBAR FUNCTION =========
def show_sidebar(df):
    
    st.sidebar.header("Filtrera ditt urval")
    st.sidebar.markdown("---")

    # Select occupation_field
    # If filter added, next selectbox will only contain relevante choices
    occupation_field = df['occupation_field'].dropna().unique()
    selected_occupation_field = st.sidebar.selectbox(
        "Välj yrkesområde:", 
        ["Alla"] + sorted(occupation_field.tolist()), 
        key="occupation_field"
    )
    if selected_occupation_field != "Alla":
        df = df[df["occupation_field"] == selected_occupation_field]    

    # Select occupation_group 
    occupation_group = df['occupation_group'].dropna().unique()
    selected_occupation_group = st.sidebar.selectbox(
        "Välj yrkesgrupp:", 
        ["Alla"] + sorted(occupation_group.tolist())
    )
    if selected_occupation_group != "Alla":
        df = df[df["occupation_group"] == selected_occupation_group]
    
    # Select occupation. 
    occupation = df['occupation'].dropna().unique()
    selected_occupation = st.sidebar.selectbox(
        "Välj yrkestitel:", 
        ["Alla"] + sorted(occupation.tolist())
    )
    
    # Select region
    region = df['workplace_region'].dropna().unique()
    selected_region = st.sidebar.selectbox(
        "Välj län:", 
        ["Alla"] + sorted(region.tolist())
    )
    
    # Select employment type
    employment_type = df['employment_type'].dropna().unique()
    selected_employment_type = st.sidebar.selectbox(
        "Välj anställningsform:", 
        ["Alla"] + sorted(employment_type.tolist())
    )
    
    # Checkboxes for aux-attributes
    st.sidebar.markdown("**Övriga krav**")
    driving_license = st.sidebar.checkbox("Körkort krävs", value=False, key="driving_license_required")    
    own_car = st.sidebar.checkbox("Egen bil krävs", value=False, key="own_car_required")    
    experience = st.sidebar.checkbox("Erfarenhet krävs", value=False, key="experience_required")

    if st.sidebar.button("Rensa filter"):
        reset_sidebar_filters()  

    # Return as a dict
    return {
        "occupation_field": selected_occupation_field,
        "occupation_group": selected_occupation_group,
        "occupation": selected_occupation,
        "region": selected_region,
        "employment_type": selected_employment_type,
        "driving_license_required": driving_license,
        "own_car_required": own_car,
        "experience_required": experience
    }

# ========= FILTER FUNCTION ==========
def apply_filters(df, filters):
    filtered = df.copy()    

    if filters["occupation_field"] != "Alla":
        filtered = filtered[filtered["occupation_field"] == filters["occupation_field"]]
    
    if filters["occupation_group"] != "Alla":
        filtered = filtered[filtered["occupation_group"] == filters["occupation_group"]]

    if filters["occupation"] != "Alla":
        filtered = filtered[filtered["occupation"] == filters["occupation"]]
    
    if filters["region"] != "Alla":
        filtered = filtered[filtered["workplace_region"] == filters["region"]]
    
    if filters["employment_type"] != "Alla":
        filtered = filtered[filtered["employment_type"] == filters["employment_type"]]
    
    if filters["driving_license_required"]:
        filtered = filtered[filtered["driving_license_required"] == True]

    if filters["own_car_required"]:
        filtered = filtered[filtered["own_car_required"] == True]

    if filters["experience_required"]:
        filtered = filtered[filtered["experience_required"] == True]
    
    return filtered

# ========= DISPLAY DATAFRAME FUNCTION ===========
def display_dataframe(filtered_df):
    
    show_columns = {
        "publication_date": "Publiceringsdatum",
        "headline": "Rubrik",
        "employer_name": "Arbetsgivare",
        "occupation": "Yrkestitel",
        "occupation_group": "Yrkesområde",
        "workplace_region": "Län",
        "application_deadline": "Sista ansökningsdag",        
    }
    display_df = (
        filtered_df
        .sort_values("publication_date", ascending=False)
        [list(show_columns.keys())]
        .rename(columns=show_columns)               
    )
    return display_df


# ======== SHOW MAPS AND METRICS ==========

def display_map_and_charts(df, selected_field):
    left_col, right_col = st.columns(2)

    # ----------- Map (right hand column) -----------
    with right_col:
        st.markdown("### Lediga tjänster per län - Alla")
        if not df.empty:
            create_hr_map(df, selected_field)
        else:
            st.warning("Ingen data att visa på kartan!")

    # ----------- Diagram (left hand column) ----------
    with left_col:
        gradient_colors = ["#F2F8FC", "#DBE8F5", "#BAD7EA", "#3C7EB9", "#2C4E80"]

        # ---- Top 5 occupation ----
        st.markdown("### Topp 5 yrkestitlar")
        top_jobs = df["occupation"].value_counts().head(5).reset_index()
        top_jobs.columns = ["Yrkestitel", "Antal"]

        fig1 = px.bar(
            top_jobs,
            x="Antal",
            y="Yrkestitel",
            orientation="h",
            text="Antal",
            color="Antal",
            color_continuous_scale=gradient_colors,
        )

        fig1.update_layout(
            margin=dict(l=120, r=20, t=20, b=40),
            xaxis_title="Antal",
            yaxis_title="Yrkestitel",
            yaxis=dict(tickangle=0),
            coloraxis_colorbar=dict(title="Antal annonser"),
            height=300,
        )

        fig1.update_traces(
            textposition="outside",
            cliponaxis=False
        )

        st.plotly_chart(fig1, use_container_width=True)

        # ---- Top 5 regions ----
        st.markdown("### Topp 5 län")
        top_regions = df["workplace_region"].value_counts().head(5).reset_index()
        top_regions.columns = ["Län", "Antal"]

        fig2 = px.bar(
            top_regions,
            x="Antal",
            y="Län",
            orientation="h",
            text="Antal",
            color="Antal",
            color_continuous_scale=gradient_colors,
        )

        fig2.update_layout(
            margin=dict(l=120, r=20, t=20, b=40),
            xaxis_title="Antal",
            yaxis_title="Län",
            yaxis=dict(tickangle=0),
            coloraxis_colorbar=dict(title="Antal annonser"),
            height=300,
        )

        fig2.update_traces(
            textposition="outside",
            cliponaxis=False
        )

        st.plotly_chart(fig2, use_container_width=True)
    
def display_metrics(df):
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

    # ----- Metric that shows last data ingestion -----
    with metric_col1:
        latest = get_latest_ingestion()
        if latest:
            st.metric("Senast uppdaterad", latest.strftime("%Y-%m-%d"))
        else:
            st.warning("Kunde inte läsa uppdateringsdatum.")

    # ----- Metric that shows num of ads -----
    with metric_col2:
        st.metric("Antal annonser", len(df))      

    # ----- Metric that shows top occupation -----
    with metric_col3:
        top_occupation = df['occupation'].value_counts().idxmax()
        count = df['occupation'].value_counts().max()
        st.metric("Yrket med flest annonser", top_occupation, help=f"{count} annonser")

    # ----- Metric that shows top region -----
    with metric_col4:        
        top_region = df['workplace_region'].value_counts().idxmax()
        count = df['workplace_region'].value_counts().max()
        st.metric("Länet med flest annonser", top_region, help=f"{count} annonser")

    st.markdown("---")

# ============== MAIN FUNCTION =================

def main():
    st.set_page_config(page_title= "HR Analytics Dashboard", layout = "wide")
    st.title("HR Analytics Dashboard")
    st.markdown("---")

    df = load_data("mart.mart_all_jobs")      
    filters = show_sidebar(df)    
    filtered_df = apply_filters(df, filters)

    display_metrics(filtered_df)
    display_map_and_charts(filtered_df, filters["occupation_field"])  
    st.dataframe(display_dataframe(filtered_df))

if __name__ == "__main__":
    main()




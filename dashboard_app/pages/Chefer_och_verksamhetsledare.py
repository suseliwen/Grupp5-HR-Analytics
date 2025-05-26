import streamlit as st
from utils import DataBase_Connection
import pandas as pd
import plotly.express as px


# ======== PAGE CONFIGURATION ========
st.set_page_config(page_title="Chefer och verksamhetsledare", layout="wide")

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
try:
    load_css('./styles/style.css')
except Exception as e:
    print(f"Kunde inte ladda in style.css: {e}")


# ======== DATA LOADING FUNCTIONS ========
def load_leadership_data():
    """Loads data for managers and business leaders from the database"""
    try:
        with DataBase_Connection() as conn:
            # print("Available tables:", available_tables)
            df = conn.execute("SELECT * FROM mart.mart_leadership_jobs").fetchdf()                    
        # Convert date columns if they exist
        for date_col in ['application_deadline', 'publication_date']:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col])
                if df[date_col].dt.tz is not None:
                    df[date_col] = df[date_col].dt.tz_localize(None)
        # Add flag for open jobs
        if 'application_deadline' in df.columns:
            df['is_open'] = df['application_deadline'] >= pd.Timestamp.now()
        return df
    
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()


# ======== METRICS VISUALIZATION FUNCTIONS ========
def show_leadership_metrics(df, filtered_df=None):
    """Displays key metrics for leadership roles"""
    if filtered_df is None:
        filtered_df = df
    
    if filtered_df.empty:
        st.warning("Inga annonser matchar filtren")
        return
    
    total_jobs = len(df)
    filtered_jobs = len(filtered_df)
    active_jobs = filtered_df['is_open'].sum() if 'is_open' in filtered_df.columns else "Okänt"
    unique_occupations = filtered_df['occupation'].nunique() if 'occupation' in filtered_df.columns else 0
    unique_employers = filtered_df['employer_name'].nunique() if 'employer_name' in filtered_df.columns else 0
    unique_regions = filtered_df['workplace_region'].nunique() if 'workplace_region' in filtered_df.columns else 0  
    # Filter out "Ingen data" from regions count
    if 'workplace_region' in filtered_df.columns:
        regions_clean = filtered_df[filtered_df['workplace_region'] != 'Ingen data']['workplace_region']
        unique_regions = regions_clean.nunique()
    else:
        unique_regions = 0   
    # Display metrics
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)
    
    col1.metric("Totala chefsannonser", filtered_jobs)
    col2.metric("Aktiva annonser", active_jobs)
    col3.metric("Unika chefsroller", unique_occupations)
    col4.metric("Unika arbetsgivare", unique_employers)
    col5.metric("Län med chefsannonser", unique_regions)
    # Show percentage of open jobs
    if isinstance(active_jobs, (int, float)) and filtered_jobs > 0:
        percent_open = (active_jobs / filtered_jobs) * 100
        col6.metric("Procent öppna jobb", f"{percent_open:.1f}%")    
    # Information about filtering
    if filtered_jobs < total_jobs:
        st.info(f"**Filtrerad vy:** Visar {filtered_jobs} av totalt {total_jobs} annonser baserat på valda filter.")


# ======== CHART VISUALIZATION FUNCTIONS ========
def show_role_chart(df):
    """Displays chart for the most common leadership roles"""
    if 'occupation' not in df.columns or df.empty:
        st.warning("Rolldiagram kan inte visas: yrkesdata saknas")
        return
    
    st.subheader("Topp 10 chefsroller nationellt")    
    # Container with border and class for CSS styling
    with st.container():
        st.markdown('<div class="role-chart-container">', unsafe_allow_html=True)
    
    role_counts = df['occupation'].value_counts().head(10).reset_index()
    role_counts.columns = ['Chefsroll', 'Antal']
    
    fig = px.bar(
        role_counts,
        x='Antal',
        y='Chefsroll',
        orientation='h',
        title="Mest efterfrågade chefsroller",
        labels={'Chefsroll': 'Chefsroll', 'Antal': 'Antal annonser'},
        color='Antal',
        color_continuous_scale=px.colors.sequential.Reds
    )
    
    fig.update_traces(textposition='outside', texttemplate='%{x}')
    fig.update_layout(
        yaxis=dict(autorange="reversed"),
        margin=dict(l=20, r=20, t=30, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    # Close the container
    st.markdown('</div>', unsafe_allow_html=True)


def show_region_chart(df):
    """Displays chart for counties with the most leadership job listings"""
    if 'workplace_region' not in df.columns or df.empty:
        st.warning("Länsdiagram kan inte visas: länsdata saknas")
        return
        
    st.subheader("Topp 10 län med flest annonser")
    # Container with border and class for CSS styling
    with st.container():
        st.markdown('<div class="region-chart-container">', unsafe_allow_html=True)
    
        region_df = df[df['workplace_region'] != 'Ingen data']
        
        if region_df.empty:
            st.warning("Ingen giltig länsdata tillgänglig för visualisering")
            return
            
        region_counts = region_df['workplace_region'].value_counts().head(10).reset_index()
        region_counts.columns = ['Län', 'Antal']
        
        fig = px.bar(
        region_counts,
        x='Län',
        y='Antal',
        title="Antal chefsannonser per län",
        color='Antal',
        color_continuous_scale=px.colors.sequential.Reds
    )
    
    fig.update_traces(textposition='outside', texttemplate='%{y}')
    st.plotly_chart(fig, use_container_width=True)

# ======== CHART VISUALIZATION FUNCTIONS ========
def show_municipality_chart(df):
    """Displays chart for municipalities with the most leadership job listings"""
    st.subheader("Topp 10 kommuner med flest annonser")
    # Add container with class for CSS styling
    st.markdown('<div class="municipality-chart-container">', unsafe_allow_html=True)
    
    try:
        # First check if the DataFrame is empty
        if df.empty:
            st.info("Ingen data tillgänglig för att visa kommundiagram")
            return           
        # Only show if we have real municipality data
        if 'workplace_municipality' not in df.columns:
            st.info("Kommundata saknas - lägg till 'workplace_municipality' i mart-filen")
            return     
        # Filter real municipality data
        muni_df = df[df['workplace_municipality'].notna() & 
                    (df['workplace_municipality'] != 'Ingen data')]
        # If no valid municipality data, show info message   
        if muni_df.empty:
            st.info("Ingen kommundata tillgänglig i denna data")
            return       
        # Get municipality counts
        muni_counts = muni_df['workplace_municipality'].value_counts().head(10).reset_index()
        muni_counts.columns = ['Kommun', 'Antal']
        title = f"Topp {len(muni_counts)} kommuner med flest chefsroller"        
        # Create chart
        fig = px.bar(
            muni_counts, x='Antal', y='Kommun', orientation='h',
            title=title, color='Antal',
            color_continuous_scale=px.colors.sequential.Reds
        )
        
        fig.update_traces(textposition='outside', texttemplate='%{x}')
        fig.update_layout(yaxis=dict(autorange="reversed"))
        
        st.plotly_chart(fig, use_container_width=True)        
        # Show coverage info
        coverage = (len(muni_df) / len(df)) * 100
        st.caption(f"{len(muni_df)}/{len(df)} jobb ({coverage:.1f}%) har kommun-info")
        
    except Exception as e:
        st.error("Kunde inte visa kommundiagram")
        print(f"Municipality chart error: {e}")
    finally:
        st.markdown('</div>', unsafe_allow_html=True)

# ======== CHART VISUALIZATION FUNCTIONS ========
def show_trend_chart(df):
    """Displays trend chart for leadership recruitment over time."""
    if 'publication_date' not in df.columns or df.empty:
        st.warning("Trenddiagram kan inte visas: publiceringsdatum saknas")
        return
        
    st.subheader("Trend för chefsrekryteringar")
    
    st.markdown('<div class="trend-chart-container">', unsafe_allow_html=True)
    
    # Create copy and convert dates first
    df_copy = df.copy()
    df_copy['publication_date'] = pd.to_datetime(df_copy['publication_date'])
    
    # Filter data to only include years 2020-2025
    df_copy = df_copy[(df_copy['publication_date'].dt.year >= 2020) & 
                      (df_copy['publication_date'].dt.year <= 2025)]
    
    if df_copy.empty:
        st.warning("Ingen data tillgänglig för åren 2020-2025")
        return
    
    # Let user choose time granularity
    time_granularity = st.selectbox(
        "Välj tidsintervall:", 
        ["Dag", "Vecka", "Månad", "År"], 
        index=2  # Default to "Månad"
    )
    
    # Group by selected time period
    if time_granularity == "Dag":
        # Group by actual date
        trend_data = df_copy.groupby(df_copy['publication_date'].dt.date).size().reset_index(name='count')
        trend_data['publication_date'] = pd.to_datetime(trend_data['publication_date'])
        x_label = "Datum"
        title = "Chefsrekrytering per dag"
        tick_format = "%Y-%m-%d"
        
    elif time_granularity == "Vecka":
        # Group by week
        df_copy['period'] = df_copy['publication_date'].dt.to_period('W')
        trend_data = df_copy.groupby('period').size().reset_index(name='count')
        trend_data['period'] = trend_data['period'].dt.to_timestamp()
        trend_data = trend_data.rename(columns={'period': 'publication_date'})
        x_label = "Vecka"
        title = "Chefsrekrytering per vecka"
        tick_format = "%Y-%m"
        
    elif time_granularity == "Månad":
        # Group by month
        df_copy['period'] = df_copy['publication_date'].dt.to_period('M')
        trend_data = df_copy.groupby('period').size().reset_index(name='count')
        trend_data['period'] = trend_data['period'].dt.to_timestamp()
        trend_data = trend_data.rename(columns={'period': 'publication_date'})
        x_label = "Månad"
        title = "Chefsrekrytering per månad"
        tick_format = "%Y-%m"
        
    else:
        # Group by year
        df_copy['year'] = df_copy['publication_date'].dt.year
        trend_data = df_copy.groupby('year').size().reset_index(name='count')        
        # Fill missing years with 0
        all_years = pd.DataFrame({'year': range(2020, 2026)})
        trend_data = all_years.merge(trend_data, on='year', how='left').fillna(0)
        trend_data = trend_data.rename(columns={'year': 'publication_date'})
        x_label = "År"
        title = "Chefsrekrytering per år"
        tick_format = "%Y"   
    # Check if we have enough data points
    if len(trend_data) < 2:
        st.warning(f"Inte tillräckligt med data för {time_granularity.lower()}svis analys")
        return    
    # Create the plot
    fig = px.line(
        trend_data,
        x='publication_date',
        y='count',
        title=title,
        labels={'publication_date': x_label, 'count': 'Antal annonser'}
    )
    
    fig.update_traces(mode='lines+markers')
    fig.update_xaxes(tickformat=tick_format)    
    # Add some styling
    if time_granularity == "År":
        fig.update_xaxes(dtick=1, range=[2019.5, 2025.5])
    
    st.plotly_chart(fig, use_container_width=True)   
    # Show some statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Totalt antal annonser", int(trend_data['count'].sum()))
    with col2:
        st.metric("Genomsnitt per period", f"{trend_data['count'].mean():.1f}")
    with col3:
        max_period = trend_data.loc[trend_data['count'].idxmax(), 'publication_date']
        if time_granularity == "År":
            max_period_str = str(int(max_period))
        else:
            max_period_str = pd.to_datetime(max_period).strftime('%Y-%m-%d')
        st.metric("Mest aktiva period", max_period_str)

    st.markdown('</div>', unsafe_allow_html=True)


def show_sector_distribution(df):
    """Shows distribution between public and private sector"""    
    st.subheader("Sektorsfördelning")
    
    st.markdown('<div class="sector-chart-container">', unsafe_allow_html=True)
    
    try:
        if df.empty:
            st.info("Ingen data tillgänglig för att visa sektorsfördelning")
            return
            
        if 'employer_name' not in df.columns:
            st.info("Arbetsgivar-data saknas i datasetet")
            return
            
        # Kategorisera sektor baserat på arbetsgivare
        def categorize_sector(employer):
            if pd.isna(employer):
                return 'Okänd'
            employer_lower = str(employer).lower()
            
            # - Offentlig sektor
            if any(word in employer_lower for word in ['kommun', 'region', 'landsting', 'statlig', 'myndighet', 'förvaltning', 'styrelsens']):
                return 'Offentlig sektor'
            # - Konsult/Bemanning
            elif any(word in employer_lower for word in ['konsult', 'bemanning', 'rekrytering', 'consulting', 'interim']):
                return 'Konsult/Bemanning'
            # - Privat sektor (allt annat)
            else:
                return 'Privat sektor'       
        # Applicera kategorisering
        df_temp = df.copy()
        df_temp['sector'] = df_temp['employer_name'].apply(categorize_sector)        
        # Filtrera bort okända för tydligare analys
        sector_df = df_temp[df_temp['sector'] != 'Okänd']
        
        if sector_df.empty:
            st.info("Ingen giltig sektordata tillgänglig")
            return
            
        sector_counts = sector_df['sector'].value_counts()       
        # Röda toner för att matcha dashboard-temat
        custom_reds = px.colors.sequential.Reds[2:7]
        
        fig = px.pie(
            values=sector_counts.values,
            names=sector_counts.index,
            title="Sektorsfördelning av chefsroller",
            color_discrete_sequence=custom_reds,
            hole=0.4
        )
        
        fig.update_traces(
            textposition="inside", 
            textinfo="percent+label",
            textfont_size=12
        )
        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.01
            ),
            margin=dict(l=20, r=80, t=60, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)      
        # Visa insikter
        total_with_sector = len(sector_df)
        total_jobs = len(df)
        coverage = (total_with_sector / total_jobs) * 100       
        # Coverage info
        st.caption(f"{total_with_sector}/{total_jobs} jobb ({coverage:.1f}%) har sektordata")
        
    except Exception as e:
        st.error("Kunde inte visa sektorsfördelning")
        print(f"Sector chart error: {e}")
        
    finally:
        st.markdown('</div>', unsafe_allow_html=True)


# ======== DATA TABLE FUNCTIONS ========
def show_jobs_table(df):
    """Displays paginated table with leadership job listings"""
    if df.empty:
        st.warning("Ingen data tillgänglig att visa i tabellen")
        return
        
    st.subheader("Alla chefsannonser")   
    # Add container with class for CSS styling
    st.markdown('<div class="jobs-table-container">', unsafe_allow_html=True)   
    
    # Select available columns to display - Updated based on actual data structure
    display_columns = ['publication_date', 'application_deadline', 'headline', 'occupation', 'employer_name', 'workplace_region']
    
    if 'is_open' in df.columns:
        display_columns.append('is_open')
    
    # Add application_url if available
    if 'application_url' in df.columns:
        display_columns.append('application_url')
    
    available_columns = [col for col in display_columns if col in df.columns]
    
    if not available_columns:
        st.warning("Inga kolumner tillgängliga att visa")
        return
    
    # Create display dataframe
    display_df = df[available_columns].copy()   
    
    # Format dates - BOTH publication_date and application_deadline
    for date_col in ['publication_date', 'application_deadline']:
        if date_col in display_df.columns:
            display_df[date_col] = pd.to_datetime(display_df[date_col]).dt.strftime('%Y-%m-%d')   
    
    # Create clickable application links if URL column exists
    if 'application_url' in display_df.columns:
        def create_link(url):
            if pd.isna(url) or url == 'Ingen data' or url == '':
                return '❌'
            else:
                return f'<a href="{url}" target="_blank">🔗 Ansök</a>'
        
        display_df['Ansök'] = display_df['application_url'].apply(create_link)
        # Remove the raw URL column from display
        display_df = display_df.drop('application_url', axis=1)
    
    # Correct column renaming based on actual data
    column_rename = {
        'publication_date': 'Publiceringsdatum',
        'headline': 'Rubrik',
        'occupation': 'Chefsroll',
        'employer_name': 'Arbetsgivare',
        'workplace_region': 'Län',
        'application_deadline': 'Sista ansökningsdag',
        'is_open': 'Öppen för ansökan'
    }
    
    rename_dict = {k: v for k, v in column_rename.items() if k in display_df.columns}
    display_df = display_df.rename(columns=rename_dict)   
    
    # Convert is_open to Yes/No
    if 'Öppen för ansökan' in display_df.columns:
        display_df['Öppen för ansökan'] = display_df['Öppen för ansökan'].map({True: 'Ja', False: 'Nej'}) 
    
    # Pagination
    rows_per_page = 10
    total_rows = len(display_df)
    total_pages = max(1, (total_rows - 1) // rows_per_page + 1)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        page = st.number_input("Sida", min_value=1, max_value=total_pages, value=1, step=1)
    
    start_idx = (page - 1) * rows_per_page
    end_idx = min(start_idx + rows_per_page, total_rows)
    
    with col1:
        st.markdown(f"Visar annonser **{start_idx + 1}–{end_idx}** av totalt **{total_rows}**")
    # Display table - use HTML if we have clickable links, otherwise use dataframe
    table_data = display_df.iloc[start_idx:end_idx]
    
    if 'Ansök' in table_data.columns:
        # Create HTML table with styling
        html_table = table_data.to_html(
            escape=False, 
            index=False, 
            classes='styled-table',
            table_id='jobs-table'
        )
        st.markdown(html_table, unsafe_allow_html=True)
    else:
        # Fallback to regular dataframe
        st.dataframe(table_data, use_container_width=True)
    
    #=== Download button ===
    # For CSV, use original data without HTML formatting
    csv_df = display_df.copy()
    if 'Ansök' in csv_df.columns:
        csv_df = csv_df.drop('Ansök', axis=1)  # Remove HTML column from CSV
    
    csv = csv_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Ladda ner data som CSV",
        data=csv,
        file_name="chefsroller_data.csv",
        mime="text/csv",
    )  
    
    # Close the container
    st.markdown('</div>', unsafe_allow_html=True)


# ======== RESET FILTERING FUNCTIONS ========
def reset_filters():
    """Reset all filter-related session state keys"""
    filter_keys = [
        'show_only_open',
        'selected_regions',
        'selected_cities',
        'selected_occupations',
        'selected_employers',
        'selected_employment_types'
    ]
    # Remove all filter-related keys from session state
    for key in filter_keys:
        if key in st.session_state:
            del st.session_state[key]

    st.sidebar.success("Alla filter har återställts!")

# ======== FILTERING FUNCTIONS ========
def add_sidebar_filters(df):
    """Adds filters in the sidebar and returns filtered dataframe"""
    st.sidebar.header("Filtrera jobb")
    
    # Add reset button at the top of the sidebar
    if st.sidebar.button("Återställ alla filter", type="secondary", use_container_width=True):
        reset_filters()
        st.rerun()
    
    st.sidebar.markdown("---")  # Add a separator line
    
    if df.empty:
        st.sidebar.warning("Ingen data tillgänglig för filtrering")
        return df
    
    filtered_df = df.copy()    
    # 1. Filter to show only open jobs
    if 'is_open' in df.columns:
        show_only_open = st.sidebar.checkbox(
            "Visa endast jobb som går att söka", 
            value=st.session_state.get('show_only_open', False),
            key='show_only_open'
        )
        if show_only_open:
            filtered_df = filtered_df[filtered_df['is_open']]

    # 2. Filter for counties
    if 'workplace_region' in df.columns and df['workplace_region'].nunique() > 0:
        # Remove null and "Ingen data" values from region options
        region_series = df['workplace_region'].dropna()
        regions = region_series[region_series != 'Ingen data'].unique()
        # Sort regions alphabetically
        regions = sorted(regions)
    
        selected_regions = st.sidebar.multiselect(
            'Filtrera på län', 
            regions,
            default=st.session_state.get('selected_regions', []),
            key='selected_regions'
        )
        if selected_regions:
            filtered_df = filtered_df[filtered_df['workplace_region'].isin(selected_regions)]
            
    # 3. Filter for cities
    if 'workplace_city' in df.columns and df['workplace_city'].nunique() > 0:
        # Remove null and "Ingen data" values from city options
        city_series = df['workplace_city'].dropna()
        cities = city_series[city_series != 'Ingen data'].unique()
        # Sort cities alphabetically
        cities = sorted(cities)
        
        selected_cities = st.sidebar.multiselect(
            'Filtrera på stad',
            cities,
            default=st.session_state.get('selected_cities', []),
            key='selected_cities'
        )
        if selected_cities:
            filtered_df = filtered_df[filtered_df['workplace_city'].isin(selected_cities)]
    
    # 4. Filter for leadership roles
    if 'occupation' in df.columns and df['occupation'].nunique() > 0:
        occupation_series = df['occupation'].dropna()
        occupations = occupation_series[occupation_series != 'Ingen data'].unique()
        occupations = sorted(occupations)
        
        selected_occupations = st.sidebar.multiselect(
            'Filtrera på chefsroll', 
            occupations,
            default=st.session_state.get('selected_occupations', []),
            key='selected_occupations'
        )
        if selected_occupations:
            filtered_df = filtered_df[filtered_df['occupation'].isin(selected_occupations)]
    
    # 5. Filter for employers
    if 'employer_name' in df.columns and df['employer_name'].nunique() > 0:
        # Remove null and "Ingen data" values from employer options
        employer_series = df['employer_name'].dropna()
        employers = employer_series[employer_series != 'Ingen data'].unique()
        # Sort employers alphabetically
        employers = sorted(employers)
        
        selected_employers = st.sidebar.multiselect(
            'Filtrera på arbetsgivare', 
            employers,
            default=st.session_state.get('selected_employers', []),
            key='selected_employers'
        )
        if selected_employers:
            filtered_df = filtered_df[filtered_df['employer_name'].isin(selected_employers)]
            
    # 6. Filter for employment type
    if 'employment_type' in df.columns and df['employment_type'].notna().any():
        employment_types = df['employment_type'].dropna()
        employment_types = employment_types[employment_types != 'Ingen data'].unique()
        employment_types = sorted(employment_types)
        
        if employment_types:
            selected_employment_types = st.sidebar.multiselect(
                'Filtrera på anställningstyp',
                employment_types,
                default=st.session_state.get('selected_employment_types', []),
                key='selected_employment_types'
            )
            
            if selected_employment_types:
                filtered_df = filtered_df[filtered_df['employment_type'].isin(selected_employment_types)]
    
    # Show count after filtering
    if len(filtered_df) < len(df):
        st.sidebar.markdown(f"**{len(filtered_df)}** jobb matchar filtren")
    
    return filtered_df
    
    
# ======== MAIN APPLICATION ========
def main():
    st.title("Chefer och verksamhetsledare")
    
    st.markdown("""
    ### Marknadsinsikter för Chefsrekrytering
    
    Detta verktyg ger dig insikter i chefsmarknaden genom analys av jobbannonser, geografiska mönster och rekryteringstrender.
    """)
    
    try:
        # Load data
        df = load_leadership_data()
        
        if df.empty:
            st.error("Kunde inte ladda data för chefer och verksamhetsledare. Databasen kan vara tom eller ha anslutningsproblem.")
            return
        # Add filters in sidebar
        filtered_df = add_sidebar_filters(df)
        
        # ======== KEY METRICS SECTION ========
        show_leadership_metrics(df, filtered_df)
               
        # ======== VISUALIZATION TABS ========
        # Add tabs for visualizations
        st.markdown('<div class="visualizations-section">', unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Chefsroller och geografi", "Trendanalys"])
        
        with tab1:
            # Display visualizations in two columns
            col1, col2 = st.columns(2)
            with col1:
                show_role_chart(filtered_df)
            with col2:
                show_region_chart(filtered_df)
            
            col1, col2 = st.columns(2)
            with col1:
                show_municipality_chart(filtered_df)
            with col2:
                show_sector_distribution(filtered_df) 
        
        with tab2:
            # Display trend chart for the entire dataset (or filtered if we want)
            show_trend_chart(filtered_df)
        # Close the visualizations section
        st.markdown('</div>', unsafe_allow_html=True) 
        
        # ======== DATA TABLE SECTION ========
        show_jobs_table(filtered_df)
            
    except Exception as e:
        st.error(f"Ett fel uppstod när applikationen kördes: {e}")
        st.info("Vänligen kontrollera databasanslutningen och försök igen senare.")

# Run the main function when the page loads
if __name__ == "__main__":
    main()
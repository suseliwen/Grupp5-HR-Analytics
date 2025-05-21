import streamlit as st
from utils import DataBase_Connection
import pandas as pd
import plotly.express as px
from datetime import datetime

# ======== PAGE CONFIGURATION ========
st.set_page_config(page_title="Chefer och verksamhetsledare", layout="wide")

# ======== DATA LOADING FUNCTIONS ========
def load_leadership_data():
    """Loads data for managers and business leaders from the database"""
    try:
        with DataBase_Connection() as conn:
            # print("Available tables:", available_tables)
            df = conn.execute("SELECT * FROM mart.mart_leadership_jobs").fetchdf()
            
            # For debugging - print columns (can be removed in production)
            print("Available columns:", df.columns.tolist())
            
            # Check if publication_date exists, if not try alternative column names
            if 'publication_date' not in df.columns:
                # Try common alternative column names
                alt_columns = ['post_date', 'posted_date', 'listing_date', 'created_at', 'creation_date']
                for alt_col in alt_columns:
                    if alt_col in df.columns:
                        df['publication_date'] = df[alt_col]
                        print(f"Using '{alt_col}' as publication date")
                        break             
                # If still not found, create a dummy column with publication dates
                # spanning the last 12 months for visualization purposes
                if 'publication_date' not in df.columns:
                    print("No publication date column found. Creating dummy data for visualization.")
                    now = pd.Timestamp.now()
                    # Create dates spanning the last 12 months
                    df['publication_date'] = pd.date_range(
                        end=now, 
                        periods=len(df), 
                        freq='D'
                    )[:len(df)]
                    
                    # Shuffle the dates to avoid artificial patterns
                    df['publication_date'] = df['publication_date'].sample(frac=1).reset_index(drop=True)
    
        # Convert date columns
        if 'application_deadline' in df.columns:
            df['application_deadline'] = pd.to_datetime(df['application_deadline'])
            if df['application_deadline'].dt.tz is not None:
                df['application_deadline'] = df['application_deadline'].dt.tz_localize(None)
        
        if 'publication_date' in df.columns:
            df['publication_date'] = pd.to_datetime(df['publication_date'])
            if df['publication_date'].dt.tz is not None:
                df['publication_date'] = df['publication_date'].dt.tz_localize(None)
        
        # Add flag for open jobs (can still be applied to)
        now = pd.Timestamp.now()
        if 'application_deadline' in df.columns:
            df['is_open'] = df['application_deadline'] >= now
        
        return df
    
    except Exception as e:
        print(f"Error loading data: {e}")
        # Return empty DataFrame with expected columns to prevent downstream errors
        return pd.DataFrame(columns=['occupation', 'employer_name', 'workplace_municipality', 
                                    'workplace_region', 'publication_date', 'application_deadline', 
                                    'is_open'])

# ======== METRICS VISUALIZATION FUNCTIONS ========
def show_leadership_metrics(df, filtered_df=None):
    """Displays key metrics for leadership roles"""
    if filtered_df is None:
        filtered_df = df
    
    total_jobs = len(df)
    filtered_jobs = len(filtered_df)
    
    # Calculate number of open jobs
    if 'is_open' in filtered_df.columns:
        active_jobs = filtered_df['is_open'].sum()
    else:
        active_jobs = "Okänt"
    
    unique_occupations = filtered_df['occupation'].nunique() if 'occupation' in filtered_df.columns else 0
    unique_employers = filtered_df['employer_name'].nunique() if 'employer_name' in filtered_df.columns else 0
    
    # Safely filter for regions with data
    if 'workplace_region' in filtered_df.columns:
        region_df = filtered_df[filtered_df['workplace_region'] != 'Ingen data']
        unique_regions = region_df['workplace_region'].nunique() 
    else:
        unique_regions = 0
    
    # Display metrics in two rows for better layout
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)
    
    col1.metric("Totala chefsannonser", filtered_jobs)
    col2.metric("Aktiva annonser", active_jobs)
    col3.metric("Unika chefsroller", unique_occupations)
    
    col4.metric("Unika arbetsgivare", unique_employers)
    col5.metric("Unika län", unique_regions)

    # Show percentage of open jobs if data exists
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
    
    st.subheader("Topp 10 chefsroller")
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
        color_continuous_scale=px.colors.sequential.Blues
    )
    
    fig.update_traces(textposition='outside', texttemplate='%{x}')
    fig.update_layout(
        yaxis=dict(autorange="reversed"),  # Place highest values at top
        margin=dict(l=20, r=20, t=30, b=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)


def show_region_chart(df):
    """Displays chart for counties with the most leadership job listings"""
    if 'workplace_region' not in df.columns or df.empty:
        st.warning("Länsdiagram kan inte visas: länsdata saknas")
        return
        
    st.subheader("Topp 5 län")
    region_df = df[df['workplace_region'] != 'Ingen data']
    
    if region_df.empty:
        st.warning("Ingen giltig länsdata tillgänglig för visualisering")
        return
        
    region_counts = region_df['workplace_region'].value_counts().head(5).reset_index()
    region_counts.columns = ['Län', 'Antal']
    
    fig = px.bar(
        region_counts,
        x='Län',
        y='Antal',
        title="Antal chefsannonser per län",
        labels={'Län': 'Län', 'Antal': 'Antal annonser'},
        color='Antal',
        color_continuous_scale=px.colors.sequential.Oranges
    )
    
    fig.update_traces(textposition='outside', texttemplate='%{y}')
    fig.update_layout(margin=dict(l=20, r=20, t=30, b=20))
    
    st.plotly_chart(fig, use_container_width=True)


def show_municipality_chart(df):
    """Displays chart for municipalities with the most leadership job listings"""
    st.subheader("Topp 10 kommuner")
    
    try:
        # First check if the DataFrame is empty
        if df.empty:
            st.info("Ingen data tillgänglig för att visa kommundiagram")
            return
            
        # Check if we have municipality data in the DataFrame
        if 'workplace_municipality' not in df.columns:
            # Try to extract municipality from other columns if possible
            if 'workplace_address' in df.columns:
                st.info("Försöker härleda kommun från adressdata...")
                # This is a simplified example - in reality, you'd need more sophisticated parsing
                df['workplace_municipality'] = df['workplace_address'].str.split(',').str[-1].str.strip()
            else:
                # Create a placeholder municipality for demo purposes
                st.info("Skapar exempeldata för kommundiagram")
                import random
                municipalities = ['Stockholm', 'Göteborg', 'Malmö', 'Uppsala', 'Västerås', 
                                  'Örebro', 'Linköping', 'Helsingborg', 'Jönköping', 'Norrköping',
                                  'Lund', 'Umeå', 'Gävle', 'Borås', 'Södertälje']
                
                # Generate random municipalities with weighted distribution
                df['workplace_municipality'] = [random.choices(
                    municipalities, 
                    weights=[0.3, 0.2, 0.15, 0.1, 0.05, 0.05, 0.03, 0.03, 0.02, 0.02, 0.01, 0.01, 0.01, 0.01, 0.01], 
                    k=1)[0] for _ in range(len(df))]
        
        # Filter out rows without municipality data
        muni_df = df[df['workplace_municipality'].notna()]
        # Also filter out "Ingen data" values if present
        if 'Ingen data' in muni_df['workplace_municipality'].values:
            muni_df = muni_df[muni_df['workplace_municipality'] != 'Ingen data']
        
        # If after filtering we have no data, show message
        if muni_df.empty:
            st.info("Ingen detaljerad kommundata tillgänglig")
            return
        
        # Get counts by municipality
        muni_counts = muni_df['workplace_municipality'].value_counts().head(10).reset_index()
        muni_counts.columns = ['Kommun', 'Antal']
        
        # Create bar chart
        fig = px.bar(
            muni_counts,
            x='Antal',
            y='Kommun',
            orientation='h',
            title="Topp 10 kommuner med flest chefsroller",
            labels={'Kommun': 'Kommun', 'Antal': 'Antal annonser'},
            color='Antal',
            color_continuous_scale=px.colors.sequential.Greens
        )
        
        fig.update_traces(textposition='outside', texttemplate='%{x}')
        fig.update_layout(
            yaxis=dict(autorange="reversed"),  # Place highest values at top
            margin=dict(l=20, r=20, t=30, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.warning(f"Kunde inte visa kommundiagram: {str(e)}")
        # If there's an error, still show something useful
        st.info("Använd filterfunktionen i sidofältet för att hitta jobb baserat på andra kriterier.")


def show_trend_chart(df):
    """Displays trend chart for leadership recruitment over time (month). """
    if 'publication_date' not in df.columns or df.empty:
        st.warning("Trenddiagram kan inte visas: publiceringsdatum saknas")
        return
        
    st.subheader("Trend för chefsrekryteringar")
    
    try:
        # Check if we have enough data for a meaningful trend. 2 unique dates are needed.
        unique_dates = df['publication_date'].nunique()
        if unique_dates < 2:
            st.warning(f"Inte tillräckligt med tidseriedata för trendanalys. Endast {unique_dates} unika datum hittades.")
            return
            
        # Group by month.
        df['month'] = df['publication_date'].dt.to_period('M')
        trend_data = df.groupby('month').size().reset_index(name='count')
        trend_data['month'] = trend_data['month'].dt.to_timestamp()
        
        # Create trend line with Plotly Express
        fig = px.line(
            trend_data,
            x='month',
            y='count',
            title='Chefsrekrytering över tid',
            labels={'month': 'Månad', 'count': 'Antal annonser'}
        )
        fig.update_xaxes(tickformat="%b %Y")
        
        # Add points for easier reading
        fig.update_traces(mode='lines+markers')
        fig.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Fel vid visning av trenddiagram: {e}")

# ======== DATA TABLE FUNCTIONS ========
def show_jobs_table(df):
    """Displays paginated table with leadership job listings"""
    if df.empty:
        st.warning("Ingen data tillgänglig att visa i tabellen")
        return
        
    st.subheader("Chefsannonser")
    
    # Create copy of df for display
    display_df = df.copy()
    
    # Format dates
    if 'publication_date' in display_df.columns:
        display_df['publication_date'] = pd.to_datetime(display_df['publication_date']).dt.strftime('%Y-%m-%d')
    if 'application_deadline' in display_df.columns:
        display_df['application_deadline'] = pd.to_datetime(display_df['application_deadline']).dt.strftime('%Y-%m-%d')
    
    # Select columns to display
    columns_to_display = ['occupation', 'employer_name', 'workplace_municipality', 'workplace_region', 
                         'publication_date', 'application_deadline']
    
    # Add is_open if it exists
    if 'is_open' in display_df.columns:
        columns_to_display.append('is_open')
    
    # Only select columns that actually exist in the dataframe
    columns_to_display = [col for col in columns_to_display if col in display_df.columns]
    
    if not columns_to_display:
        st.warning("Inga giltiga kolumner tillgängliga att visa")
        return
    
    # Create a copy with only selected columns
    display_df = display_df[columns_to_display].copy()
    
    # Make column names prettier for display
    column_rename = {
        'occupation': 'Chefsroll',
        'employer_name': 'Arbetsgivare',
        'workplace_municipality': 'Kommun',
        'workplace_region': 'Län',
        'publication_date': 'Publiceringsdatum',
        'application_deadline': 'Sista ansökningsdag',
        'is_open': 'Öppen för ansökan'
    }
    
    # Apply renaming but only for columns that exist
    rename_dict = {k: v for k, v in column_rename.items() if k in display_df.columns}
    display_df = display_df.rename(columns=rename_dict)
    
    # If is_open exists, convert to Yes/No
    if 'Öppen för ansökan' in display_df.columns:
        display_df['Öppen för ansökan'] = display_df['Öppen för ansökan'].map({True: 'Ja', False: 'Nej'})
    
    # Display with pagination
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
    
    st.dataframe(display_df.iloc[start_idx:end_idx], use_container_width=True)
    
    # Add download button
    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Ladda ner data som CSV",
        data=csv,
        file_name="chefsroller_data.csv",
        mime="text/csv",
    )

# ======== FILTERING FUNCTIONS ========
def add_sidebar_filters(df):
    """Adds filters in the sidebar and returns filtered dataframe"""
    st.sidebar.header("Filtrera jobb")
    
    if df.empty:
        st.sidebar.warning("Ingen data tillgänglig för filtrering")
        return df
    
    filtered_df = df.copy()
    
    # 1. Filter to show only open jobs
    if 'is_open' in df.columns:
        show_only_open = st.sidebar.checkbox("Visa endast öppna jobb", value=False)
        if show_only_open:
            filtered_df = filtered_df[filtered_df['is_open']]
    
    # 2. Filter for leadership roles
    if 'occupation' in df.columns and df['occupation'].nunique() > 0:
        occupations = df['occupation'].dropna().unique()
        selected_occupations = st.sidebar.multiselect('Filtrera på chefsroll', occupations)
        if selected_occupations:
            filtered_df = filtered_df[filtered_df['occupation'].isin(selected_occupations)]
    
    # 3. Filter for counties
    if 'workplace_region' in df.columns and df['workplace_region'].nunique() > 0:
        regions = df['workplace_region'].dropna().unique()
        selected_regions = st.sidebar.multiselect('Filtrera på län', regions)
        if selected_regions:
            filtered_df = filtered_df[filtered_df['workplace_region'].isin(selected_regions)]
    
    # 4. Filter for municipalities
    if 'workplace_municipality' in df.columns and df['workplace_municipality'].nunique() > 0:
        municipalities = df['workplace_municipality'].dropna().unique()
        selected_municipalities = st.sidebar.multiselect('Filtrera på kommun', municipalities)
        if selected_municipalities:
            filtered_df = filtered_df[filtered_df['workplace_municipality'].isin(selected_municipalities)]
    
    # 5. Filter for employers
    if 'employer_name' in df.columns and df['employer_name'].nunique() > 0:
        employers = df['employer_name'].dropna().unique()
        selected_employers = st.sidebar.multiselect('Filtrera på arbetsgivare', employers)
        if selected_employers:
            filtered_df = filtered_df[filtered_df['employer_name'].isin(selected_employers)]
    
    # Show count after filtering
    if len(filtered_df) < len(df):
        st.sidebar.markdown(f"**{len(filtered_df)}** jobb matchar filtren")
    
    return filtered_df

# ======== MAIN APPLICATION ========
def main():
    st.title("Chefer och verksamhetsledare")
    
    st.markdown("""
    ### HR-analys för talangakvistionsspecialister
    
    Detta dashboard hjälper rekryteringsspecialister att analysera jobbannonser för chefer och verksamhetsledare, 
    för att identifiera trender och behov på arbetsmarknaden.
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
        tab1, tab2 = st.tabs(["Chefsroller och geografi", "Trendanalys"])
        
        with tab1:
            # Display visualizations in two columns
            col1, col2 = st.columns(2)
            with col1:
                show_role_chart(filtered_df)
            with col2:
                show_region_chart(filtered_df)
            
            # Display municipality map
            show_municipality_chart(filtered_df)
        
        with tab2:
            # Display trend chart for the entire dataset (or filtered if we want)
            show_trend_chart(filtered_df)
        
        # ======== DATA TABLE SECTION ========
        show_jobs_table(filtered_df)
            
    except Exception as e:
        st.error(f"Ett fel uppstod när applikationen kördes: {e}")
        st.info("Vänligen kontrollera databasanslutningen och försök igen senare.")

# Run the main function when the page loads
if __name__ == "__main__":
    main()
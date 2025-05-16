import streamlit as st
import pandas as pd
import plotly.express as px
import json

def load_geojson():
    ### Load and return the Swedish regions GeoJSON file ###
    try:
        geojson_path = "swedish_regions.geojson"
        
        with open(geojson_path, 'r', encoding='utf-8') as f:
            regions_geo = json.load(f)
        return regions_geo
    except Exception as e:
        st.error(f"Ett fel uppstod vid laddning av GeoJSON: {e}")
        return None

def map_region_names(region_name):
    """Map region names to match GeoJSON format"""
    
    if pd.isna(region_name) or region_name == "Ej angivet":
        return None
    
    # Mapping table to handle special cases
    mapping = {
        "Stockholms län": "Stockholm",
        "Västra Götalands län": "Västra Götaland",
        "Östergötlands län": "Östergötland",
        "Skåne län": "Skåne",
        "Norrbottens län": "Norrbotten",
        "Dalarnas län": "Dalarna",
        "Örebro län": "Örebro",
        "Uppsala län": "Uppsala",
        "Västmanlands län": "Västmanland",
        "Västernorrlands län": "Västernorrland",
        "Jönköpings län": "Jönköping",
        "Västerbottens län": "Västerbotten",
        "Gävleborgs län": "Gävleborg",
        "Hallands län": "Halland",
        "Värmlands län": "Värmland",
        "Kalmar län": "Kalmar",
        "Kronobergs län": "Kronoberg",
        "Södermanlands län": "Södermanland",
        "Jämtlands län": "Jämtland",
        "Blekinge län": "Blekinge",
        "Gotlands län": "Gotland"
    }
    
    return mapping.get(region_name, region_name)

def create_hr_map(df, selected_occupation_field):
    """Create a map visualization of HR data by Swedish regions"""
    
    # Add CSS for styling
    st.markdown("""
    <style>
        .map-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #1E6091;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Load the GeoJSON file
    regions_geo = load_geojson()
    if regions_geo is None:
        return
    
    # Extract region names from GeoJSON
    actual_regions = []
    id_property = "name"  # ID property in GeoJSON
    
    for feature in regions_geo['features']:
        if id_property in feature['properties']:
            actual_regions.append(feature['properties'][id_property])
    
    # Prepare region data from dataframe
    if 'workplace_region' in df.columns:
        # Group by region and count jobs
        region_counts = df['workplace_region'].value_counts().reset_index()
        region_counts.columns = ['region', 'count']  # Using 'count' as column name to match df structure
        
        # Map region names to match GeoJSON format
        region_counts['region_id'] = region_counts['region'].apply(map_region_names)
        region_counts = region_counts[~region_counts['region_id'].isna()]
        
        # Create base dataframe with all regions
        base_regions = []
        for region in actual_regions:
            base_regions.append({
                "region_id": region,
                "vacancies": 0  # Default value
            })
        
        base_df = pd.DataFrame(base_regions)
        
        # Merge with actual data - rename count to vacancies for consistency
        region_counts = region_counts.rename(columns={'count': 'vacancies'})
        
        # Merge with actual data
        merged_df = pd.merge(
            base_df,
            region_counts[['region_id', 'vacancies']],
            on='region_id',
            how='left'
        )
        # Ensure vacancies column exists and has no NaN values
        if 'vacancies_y' in merged_df.columns:
            merged_df['vacancies'] = merged_df['vacancies_y'].fillna(0)
        else:
            merged_df['vacancies'] = merged_df['vacancies'].fillna(0)
        
        # Set color theme based on occupation field
        color_themes = {
            "Samtliga yrkesområden": "Blues",
            "Yrken med social inriktning": "Greens",
            "Yrken med teknisk inriktning": "Purples",
            "Chefer och verksamhetsledare": "Reds"
        }
        color_theme = color_themes.get(selected_occupation_field, "Blues")
        
        # Create choropleth map
        try:
            # Create map with Mapbox
            fig = px.choropleth_mapbox(
                merged_df,
                geojson=regions_geo,
                locations='region_id',
                featureidkey=f"properties.{id_property}",
                color='vacancies',
                color_continuous_scale=color_theme,
                mapbox_style="carto-positron",
                zoom=4.2,
                center={"lat": 62.5, "lon": 15},
                opacity=0.85,
                hover_name='region_id',
                hover_data={
                    'region_id': False,
                    'vacancies': True
                },
                labels={
                    'vacancies': 'Lediga tjänster',
                    'region_id': 'Län'
                }
            )
            
            # Update layout
            fig.update_layout(
                margin={"r":0, "t":0, "l":0, "b":0},
                height=900,  # Minska höjden något
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=14,
                    font_family="Arial",
                    font_color="black"
                )
            )
            
            ### COLORBAR ### 
            
            # Update color axis
            fig.update_coloraxes(
                colorbar_title_text="Antal lediga tjänster",
                colorbar_title_font_size=14,
                colorbar_tickfont_size=12
            )
            
            # Display map
            st.plotly_chart(fig, use_container_width=True)
            
        except Exception as mapbox_error:
            # Fallback to standard choropleth if Mapbox fails
            st.warning(f"Kunde inte skapa Mapbox-karta: {mapbox_error}")
            
            fig = px.choropleth(
                merged_df,
                geojson=regions_geo,
                locations='region_id',
                featureidkey=f"properties.{id_property}",
                color='vacancies',
                color_continuous_scale=color_theme,
                scope="europe",
                labels={'vacancies': 'Lediga tjänster', 'region_id': 'Län'}
            )
            
            fig.update_geos(
                center=dict(lat=62.5, lon=15),
                projection_scale=7,
                showcoastlines=True, 
                coastlinecolor="Black",
                showland=True, 
                landcolor="lightgrey"
            )
            
            fig.update_coloraxes(
                colorbar_title_text="Antal lediga tjänster"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.error("Dataframen saknar kolumnen 'workplace_region' som behövs för kartvisualiseringen.")
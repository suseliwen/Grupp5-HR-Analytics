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
        
    # Load the GeoJSON file
    regions_geo = load_geojson()
    if regions_geo is None:
        return
    
    # Extract region names from GeoJSON
    actual_regions = []
    id_property = "name"
    # Check if the id_property exists in the GeoJSON
    for feature in regions_geo['features']:
        if id_property in feature['properties']:
            actual_regions.append(feature['properties'][id_property])
    
    # Prepare region data from dataframe
    if 'workplace_region' in df.columns:
        # Group by region and count jobs
        region_counts = df['workplace_region'].value_counts().reset_index()
        region_counts.columns = ['region', 'count']       
        # Map region names to match GeoJSON format
        region_counts['region_id'] = region_counts['region'].apply(map_region_names)
        region_counts = region_counts[~region_counts['region_id'].isna()]       
        # Create base dataframe with all regions
        base_df = pd.DataFrame({'region_id': actual_regions, 'vacancies': 0})       
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
        
        # Default map settings
        map_height = 580
        zoom_level = 3.6
        font_size = 12
        margin_size = 10
        colorbar_thickness = 12
        
        # Set map center
        sweden_center = {"lat": 63.0, "lon": 17.0}
        
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
                zoom=zoom_level,
                center=sweden_center,
                opacity=0.85,
                hover_name='region_id',
                hover_data={
                    'region_id': False,
                    'vacancies': True
                },
                labels={
                    'vacancies': 'Lediga tjänster',
                    'region_id': 'Län'
                },
                title=f"Lediga tjänster per län - {selected_occupation_field}", 
            )
            
            # Update layout
            fig.update_layout(
                margin={"r": margin_size, "t": 30, "l": margin_size, "b": margin_size},
                height=map_height,
                autosize=True,
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=14,
                    font_family="Arial",
                    font_color="black"
                ),
                font=dict(size=font_size),
                title_font_size=font_size + 2
            )
            
            ### COLORBAR ###
            # Update color axis
            fig.update_coloraxes(
                colorbar_title_text="Antal lediga tjänster",
                colorbar_title_font_size=font_size,
                colorbar_tickfont_size=font_size -2,
                colorbar=dict(
                    len=0.7,
                    thickness=colorbar_thickness,
                    x=1.02,
                    xanchor="left"
                )
            )
            
            # Display the map
            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={
                'displayModeBar': True,
                'displaylogo': False,
                'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d'],
                'responsive': True,
                'toImageButtonOptions': {
                    'format': 'png',
                    'width': 500,
                    'height': 700,
                    'scale': 1
                }
            })
            st.markdown('</div>', unsafe_allow_html=True)
            
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
                labels={'vacancies': 'Lediga tjänster', 'region_id': 'Län'},
                title=f"Lediga tjänster per län - {selected_occupation_field}",
            )
            
            fig.update_geos(
                center=dict(lat=62.5, lon=15.5),
                projection_scale=3.5,
                showcoastlines=True, 
                coastlinecolor="Black",
                showland=True, 
                landcolor="lightgrey",
                lonaxis_range=[7, 26],
                lataxis_range=[54, 71]
            )
            
            fig.update_layout(
                height=map_height,
                autosize=True,
                margin={"r": margin_size, "t": 30, "l": margin_size, "b": margin_size},
                font=dict(size=font_size)
            )
            
            fig.update_coloraxes(
                colorbar_title_text="Antal lediga tjänster",
                colorbar_title_font_size=font_size,
                colorbar_tickfont_size=font_size - 2
            )
            
            # Wrap fallback map in container too
            st.markdown('<div class="map-container">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={
                'displayModeBar': True,
                'displaylogo': False,
                'responsive': True,
                'toImageButtonOptions': {
                    'format': 'png',
                    'filename': 'sweden_hr_map_fallback',
                    'height': 500,
                    'width': 700,
                    'scale': 1
                }
            })
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.error("Dataframen saknar kolumnen 'workplace_region' som behövs för kartvisualiseringen.")
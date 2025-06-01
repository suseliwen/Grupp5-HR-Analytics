import duckdb
from pathlib import Path
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st
# Importing the Google Generative AI library
import google.generativeai as genai
from dotenv import load_dotenv
import json
import os

# A specific class to handle the connection to the DuckDB.
# This class uses a context manager, to make sure  the connection is closed after use.
class DataBase_Connection:
    def __init__(self, db_filename="jobads_data_warehouse.duckdb", read_only=True):
        self.db_path = Path(__file__).parent.parent / db_filename
        self.read_only = read_only
        self.connection = None

    def __enter__(self):
        self.connection = duckdb.connect(database=self.db_path, read_only=True)
        return self.connection
    
    
    def __exit__(self, exc_type, exc_value, traceback):
        if self.connection:
            self.connection.close()


@st.cache_data(ttl=3600)  #cache data for 1 hour
def load_data(mart_table):
    now = datetime.now(ZoneInfo("Europe/Stockholm")).date()

    try:
        with DataBase_Connection() as conn:
            df = conn.execute(f"SELECT * FROM {mart_table}").fetchdf()
            df["publication_date"] = pd.to_datetime(df["publication_date"], errors="coerce").dt.date
            df["application_deadline"] = pd.to_datetime(df["application_deadline"], errors="coerce").dt.date
            df = df[df["application_deadline"] >= now]
        
        print(f"Datan laddas från {mart_table}!")  #debug print 
        return df

    except Exception as e:
        st.error(f"Fel vid inläsning av data från {mart_table}: {e}")
        return pd.DataFrame()

# Function to fetch the most recent ingestion timestamp from the staging.job_ads table
# Connects to the DuckDB database in read-only mode, and returns the latest ingestion time
def get_latest_ingestion():
    db_path = Path(__file__).parent.parent / "jobads_data_warehouse.duckdb"
    try:
        with duckdb.connect(database=db_path, read_only=True) as conn:
            result = conn.execute("""
                    SELECT MAX(ingestion_timestamp) as last_updates
                    FROM staging.job_ads
                    """).fetchone()
            return result[0] if result else None
            
    except Exception as e:
        print(f"Fel vid hämtning av data: {e}")
        return None


# === LLM FUNKTIONALITET ===
def setup_gemini():

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", None)
    
    if not api_key:
        api_key = st.sidebar.text_input("Gemini API Key:", type="password")    
    if not api_key:
        st.sidebar.error("API key required")
        return None
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        model.generate_content("Hello")
        st.sidebar.success("✅ AI Ready")
        return model
    except:
        st.sidebar.error("Invalid API key")
        return None

 
# === PROCESSING JOB TEXT WITH GEMINI ===
@st.cache_data
def analyze_job_with_gemini(job_text, occupation_field=None):
    model = setup_gemini()
    if not model:
        return None
    
    # Map occupation field to area
    area_mapping = {
        'Yrken med social inriktning': 'Social',
        'Yrken med teknisk inriktning': 'Teknisk', 
        'Chefer och verksamhetsledare': 'Chefer'
    }
    
    område = area_mapping.get(occupation_field, 'Okänt')
    # Avoid exceeding token limits
    short_job_text = job_text[:500] if len(job_text) > 500 else job_text
    
    prompt = f"""HR Analytics-specialist: Analysera jobbannons från Arbetsförmedlingen.

{short_job_text}

Returnera ENDAST giltigt JSON:
{{
    "krav": ["obligatoriska kompetenser"],
    "meriterande": ["önskvärda kompetenser"],
    "språk": ["programmeringsspråk/främmande språk"],
    "verktyg": ["mjukvaror/verktyg/plattformar"],
    "nivå": "Junior/Mid/Senior",
    "arbetstyp": "Remote/Hybrid/Office",
    "plats": ["städer"],
    "kvaliteter": ["personliga egenskaper"],
    "område": "{område}"
}}
Fokusområden:
- Chefer: Ledarskap, strategi, ekonomi, personalansvar
- Teknisk: Programmering, verktyg, system, molnplattformar  
- Social: Kommunikation, omvårdnad, service, regelkunskap
"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Gemini API fel: {e}")


# === VALIDATION OF GEMINI ANSWERS ===
def validate_gemini_response(response_text):
    if not response_text:
        return None        
    try:        
        clean_text = response_text.replace('```json', '').replace('```', '').strip()
        parsed = json.loads(clean_text)
        
        defaults = {
            'krav': [], 'meriterande': [], 'språk': [], 'verktyg': [], 
            'plats': [], 'kvaliteter': [], 'nivå': 'Unknown', 
            'arbetstyp': 'Unknown', 'område': 'Unknown'
        }        
        return {**defaults, **parsed}
    except Exception as e:
        st.warning(f"Response validation error: {str(e)}")
        return None

# ======= PROMPT FOR SOCIAL OCCUPATION =======

def gemini_chat(prompt: str) -> str:
    model = setup_gemini()
    if model is None:
        return "Fel när funktionen skulle aktiveras"
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Något gick tyvärr fel: {str(e)}"


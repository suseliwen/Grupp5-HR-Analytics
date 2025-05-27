import duckdb
from pathlib import Path
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit as st
# Importing the Google Generative AI library
import google.generativeai as genai
from dotenv import load_dotenv
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
            df = conn.execute("SELECT * FROM mart.mart_occupation_social").fetchdf()
            df["publication_date"] = pd.to_datetime(df["publication_date"], errors="coerce").dt.date
            df["application_deadline"] = pd.to_datetime(df["application_deadline"], errors="coerce").dt.date
            df = df[df["application_deadline"] >= now]
        
        print(f"Datan laddas från {mart_table}!")  #debug print 
        return df

    except Exception as e:
        st.error(f"Fel vid inläsning av data från {mart_table}: {e}")
        return pd.DataFrame()


# ========== LLM FUNKTIONALITET ==========
def setup_gemini():
    """
    Sets up the Google Generative AI with proper error handling
    """
    try:
        # Leta efter .env filen i parent directory (root av projektet)
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(env_path)       
        # Try to get API key from multiple sources
        api_key = None
        # 1. Try environment variable
        api_key = os.getenv("GEMINI_API_KEY") 
        # 2. Try Streamlit secrets (if running on Streamlit Cloud)
        if not api_key and hasattr(st, 'secrets'):
            try:
                api_key = st.secrets.get("GEMINI_API_KEY")
            except:
                pass    
        # 3. Allow manual input in sidebar if no API key found
        if not api_key:
            st.sidebar.warning("GEMINI_API_KEY not found in environment")
            api_key = st.sidebar.text_input(
                "Enter your Gemini API Key:", 
                type="password",
                help="Get your API key from https://makersuite.google.com/app/apikey"
            )           
        if not api_key:
            st.sidebar.error("❌ No API key provided")
            return None          
        # Configure Gemini
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.0-flash-exp")       
        # Test the connection
        try:
            test_response = model.generate_content("Hello")
            st.sidebar.success("✅ Gemini API connected successfully")
            return model
        except Exception as e:
            st.sidebar.error(f"❌ API key validation failed: {str(e)}")
            return None
            
    except Exception as e:
        st.sidebar.error(f"❌ Gemini setup error: {str(e)}")
        return None
# ========== PROCESSING JOB TEXT WITH GEMINI ==========
@st.cache_data
def analyze_job_with_gemini(job_text):
    """
    Analyzes the text using Gemini model.
    """
    model = setup_gemini()
    if not model:
        return None    
    prompt = f"""
Du är en HR Analytics-specialist som arbetar för en rekryteringsbyrå. Analysera denna jobbannons från Arbetsförmedlingen:

{job_text}

Returnera ENDAST giltigt JSON:
{{
    "krav": ["skill1", "skill2"],
    "meriterande": ["skill1", "skill2"],
    "språk": ["Python", "SQL"],
    "verktyg": ["Docker", "AWS"],
    "nivå": "Junior/Mid/Senior",
    "arbetstyp": "Remote/Hybrid/Office",
    "plats": ["Stockholm"],
    "kvaliteter": ["Ledarskap", "Innovation"],
    "område": "Chefer/Teknisk/Social"
}}

Anpassa efter yrkesområde:
- Chefer: Ledarskap, strategi, ekonomi
- Teknisk: Programmering, verktyg, system
- Social: Kommunikation, omvårdnad, service
"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        st.error(f"Gemini API fel: {e}")
        return analyze_job_with_gemini(job_text)
    
# ========== VALIDATION OF GEMINI ANSWERS ==========
def validate_gemini_response(response_text):
    """
    Validate and clean Gemini response
    """
    if not response_text:
        return None        
    try:
        import json
        import re       
        # Remove code blocks if present
        clean_text = re.sub(r'```json\s*', '', response_text)
        clean_text = re.sub(r'```\s*$', '', clean_text)
        clean_text = clean_text.strip()      
        # Try to parse JSON
        parsed = json.loads(clean_text)       
        # Validate required fields
        required_fields = ['krav', 'meriterande', 'språk', 'verktyg', 'nivå', 'arbetstyp', 'plats', 'kvaliteter', 'område']
        for field in required_fields:
            if field not in parsed:
                parsed[field] = [] if field in ['krav', 'meriterande', 'språk', 'verktyg', 'plats', 'kvaliteter'] else 'Unknown'               
        return parsed
        
    except json.JSONDecodeError as e:
        st.warning(f"JSON parsing error: {str(e)}")
        return None
    except Exception as e:
        st.warning(f"Response validation error: {str(e)}")
        return None
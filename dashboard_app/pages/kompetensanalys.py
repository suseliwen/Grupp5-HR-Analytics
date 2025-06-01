import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter
from pathlib import Path
import time
from utils import analyze_job_with_gemini, DataBase_Connection, setup_gemini, validate_gemini_response

st.set_page_config(page_title="AI Kompetensanalys", layout="wide")

css_file = Path('./styles/style.css')
if css_file.exists():
    st.markdown(f'<style>{css_file.read_text()}</style>', unsafe_allow_html=True)
# Occupation mapping for job tables
OCCUPATION_MAP = {
    'Yrken med social inriktning': 'mart_occupation_social',
    'Yrken med teknisk inriktning': 'mart_it_jobs',
    'Chefer och verksamhetsledare': 'mart_leadership_jobs'
}
OCCUPATION_OPTIONS = ['Alla'] + list(OCCUPATION_MAP.keys())

# === DATA LOADING FUNCTIONS ==
@st.cache_data(ttl=3600)
def load_job_data(occupation_field=None, limit=15):
    try:
        with DataBase_Connection() as conn:
            if occupation_field == 'Alla' or occupation_field is None:
                tables = list(OCCUPATION_MAP.values())
                union_queries = [f"SELECT job_id, headline, description, employer_name, occupation_field, occupation FROM mart.{table} WHERE description IS NOT NULL" for table in tables]
                query = f"({' UNION ALL '.join(union_queries)}) ORDER BY job_id DESC LIMIT {limit}"
            else:
                table = OCCUPATION_MAP.get(occupation_field, 'mart_occupation_social')
                query = f"SELECT job_id, headline, description, employer_name, occupation_field, occupation FROM mart.{table} WHERE description IS NOT NULL LIMIT {limit}"
                
            return conn.execute(query).fetchdf()
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

# === AI ANALYSIS FUNCTIONS ===
def analyze_jobs(job_df, max_jobs=5):
    results = []

    with st.status(f"Analyserar {max_jobs} jobb...", expanded=True) as status:
        for i, (_, row) in enumerate(job_df.head(max_jobs).iterrows()):
            if i > 0:
                st.write("Väntar 5 sekunder för att undvika rate limits...")
                time.sleep(5)
                
            st.write(f"Jobb {i+1}/{max_jobs}: {row['headline'][:40]}...")
            
            job_text = f"Titel: {row['headline']}\nFöretag: {row['employer_name']}\nOmråde: {row['occupation_field']}\nBeskrivning: {row['description'][:800]}..."
            
            ai_result = analyze_job_with_gemini(job_text, row.get('occupation_field'))
            if ai_result and (parsed := validate_gemini_response(ai_result)):
                results.append({**row.to_dict(), **parsed})
            else:
                st.warning(f"Misslyckades med att analysera: {row['headline'][:30]}...")
                
        status.update(label=f"✅ Klart! Analyserade {len(results)}/{max_jobs} jobb", state="complete")    
    return results

# === METRICS AND KPI FUNCTIONS ===
def create_metrics(results):
    col1, col2, col3 = st.columns(3)

    all_skills = [skill for r in results for skill in (r.get('krav', []) + r.get('meriterande', []))]
    most_common_skill = Counter(all_skills).most_common(1)[0][0] if all_skills else "Ingen data"

    total_requirements = len(all_skills)
    avg_requirements = round(total_requirements / len(results), 1) if results else 0

    metrics = [
        ("Analyserade jobb", len(results)),
        ("Mest efterfrågad kompetens", most_common_skill),
        ("Krav per jobb (snitt)", f"{avg_requirements} st")
    ]
    for col, (label, value) in zip([col1, col2, col3], metrics):
        col.metric(label, value)
        
# === VISUALIZATION FUNCTIONS ===
def create_skills_chart(results):
    all_skills = [skill for r in results for skill in (r.get('krav', []) + r.get('meriterande', []))]

    if not all_skills:
        st.info("Ingen kompetensdata att visa")
        return

    skills_count = Counter(all_skills).most_common(15)

    skills = [skill for skill, _ in skills_count]
    counts = [count for _, count in skills_count]

    fig = px.bar(
        x=counts,
        y=skills,
        orientation='h',
        title="Mest efterfrågade kompetenser",
        color=[count for _, count in skills_count],
        color_continuous_scale='viridis',
        labels={'x': 'Antal jobb', 'y': 'Kompetens', 'color': 'Efterfrågan'}
    )
    fig.update_layout(yaxis={'categoryorder': 'array', 'categoryarray': skills[::-1]}, height=600)
    st.plotly_chart(fig, use_container_width=True)

# === CONTENT GENERATION FUNCTIONS ===
def create_linkedin_content(results):

    all_skills = [skill for r in results for skill in (r.get('krav', []) + r.get('meriterande', []))]

    if len(all_skills) < 3:
        return

    skill_count = Counter(all_skills).most_common(3)
    hashtags = []
    for skill, count in skill_count:
        clean_hashtag = skill.replace(" ", "").replace("-", "").replace("å", "a").replace("ä", "a").replace("ö", "o")
        hashtags.append(f"#{clean_hashtag}")

    hashtags.extend(["#Rekrytering", "#Jobbsökning", "#HR"])

    linkedin_post = f"""Hetaste egenskaperna på arbetsmarknaden:

1️⃣ {skill_count[0][0]} ({skill_count[0][1]} jobb)
2️⃣ {skill_count[1][0]} ({skill_count[1][1]} jobb)
3️⃣ {skill_count[2][0]} ({skill_count[2][1]} jobb)

Kopiera texten nedan och publicera på LinkedIn!
{' '.join(hashtags)}"""
    
    st.subheader("LinkedIn marknadsföringsinnehåll")
    st.code(linkedin_post, language="markdown")

# === VISUALIZATION FUNCTIONS ===
def create_visualizations(results):
    if not results:
        st.warning("Ingen data att visa")
        return    
    create_metrics(results)
    st.subheader("Analysresultat")
    create_skills_chart(results)
    create_linkedin_content(results)

# === DATA EXPORT FUNCTIONS ===
def create_results_table(results):
    if not results:
        st.warning("Inga resultat att visa")
        return

    display_data = []
    for r in results:
        display_data.append({
            'Jobbtitel': (r.get('headline', 'Saknas')[:50] + '...' if len(r.get('headline', '')) > 50 else r.get('headline', 'Saknas')),
            'Företag': r.get('employer_name', 'Saknas'),
            'Område': r.get('occupation_field', 'Saknas'),
            'Nivå': r.get('nivå', 'Saknas'),
            'Kompetenser': ', '.join(r.get('krav', [])[:3]) + ('...' if len(r.get('krav', [])) > 3 else ''),
            'Språk': ', '.join(r.get('språk', [])[:3]),
            'Verktyg': ', '.join(r.get('verktyg', [])[:2]),
            'Arbetstyp': r.get('arbetstyp', 'Saknas'),
        })
    
    df = pd.DataFrame(display_data)
    st.dataframe(df, use_container_width=True)

    st.markdown("### Exportera data")
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M')

    csv_data = df.to_csv(index=False, encoding='utf-8-sig', sep=';')
    st.download_button(
        "📥 Ladda ner CSV",
        csv_data,
        f"kompetensanalys_{timestamp}.csv",
        "text/csv", 
        use_container_width=True
    )

# === MAIN APPLICATION FUNCTION ===
def main():
    st.title("AI Kompetensanalys")
    st.markdown("*Snabb AI-analys av jobbannonser med Google Gemini*")   

    with st.sidebar:
        st.header("Kontroller")       

        if not (model := setup_gemini()):
            st.error("❌ API-konfiguration krävs")
            st.stop()
        st.success("✅ AI redo")       

        selected_field = st.selectbox("Yrkesområde:", OCCUPATION_OPTIONS)
        max_jobs = st.slider("Antal jobb att analysera:", 1, 15, 3)

        st.markdown("---")
        analyze_button = st.button("Starta analys", type="primary", use_container_width=True)
        
        if 'results' in st.session_state:
            if st.button("Rensa resultat", type="secondary", use_container_width=True):
                del st.session_state['results']
                st.rerun()   

    with st.spinner("Laddar jobbdata..."):
        job_data = load_job_data(selected_field, max_jobs)
    
    if job_data.empty:
        st.error("❌ Ingen data hittades")
        st.stop()
    
    st.sidebar.info(f"{len(job_data)} jobb laddade")
    
    with st.expander(f"Förhandsvisning ({len(job_data)} jobb)", expanded=False):
        st.dataframe(job_data[['headline', 'employer_name', 'occupation_field']].head(), use_container_width=True)   

    if analyze_button:
        with st.spinner("Kör AI-analys..."):
            results = analyze_jobs(job_data, max_jobs)
        
        if results:
            st.session_state['results'] = results
            st.success(f"Analyserade {len(results)} jobb framgångsrikt!")
            st.balloons()
        else:
            st.error("❌ Analysen misslyckades") 

    if results := st.session_state.get('results'):
        st.markdown("---")
        st.subheader(f"Analysresultat ({len(results)} jobb)")
        
        tab1, tab2 = st.tabs(["Visualiseringar", "Datatabell att exportera"])
        
        with tab1:
            create_visualizations(results)        
        with tab2:
            create_results_table(results)
    else:
        st.info("Klicka på 'Starta analys' för att börja")

if __name__ == "__main__":
    main()
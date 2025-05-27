import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter
import json
from utils import analyze_job_with_gemini, DataBase_Connection, setup_gemini, validate_gemini_response

# Configuration
st.set_page_config(page_title="AI Skills Analysis", layout="wide")

# Constants
OCCUPATION_MAP = {
    'Yrken med social inriktning': 'mart_occupation_social',
    'Yrken med teknisk inriktning': 'mart_it_jobs', 
    'Chefer och verksamhetsledare': 'mart_leadership_jobs'
}

OCCUPATION_OPTIONS = ['Alla'] + list(OCCUPATION_MAP.keys())

@st.cache_data(ttl=3600)
def load_job_data(occupation_field=None, limit=15):
    """Load job data from mart tables - Simplified query building"""
    try:
        with DataBase_Connection() as conn:
            if occupation_field == 'Alla' or occupation_field is None:
                # Union query for all tables
                tables = list(OCCUPATION_MAP.values())
                union_queries = [f"SELECT job_id, headline, description, employer_name, occupation_field, occupation, workplace_region FROM mart.{table} WHERE description IS NOT NULL" for table in tables]
                query = f"({' UNION ALL '.join(union_queries)}) ORDER BY job_id DESC LIMIT {limit}"
            else:
                table = OCCUPATION_MAP.get(occupation_field, 'mart_occupation_social')
                query = f"SELECT job_id, headline, description, employer_name, occupation_field, occupation, workplace_region FROM mart.{table} WHERE description IS NOT NULL LIMIT {limit}"
            
            return conn.execute(query).fetchdf()
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

def analyze_jobs(job_df, max_jobs=5):
    """Streamlined AI analysis with better progress tracking"""
    results = []
    
    with st.status(f"Analyzing {max_jobs} jobs...", expanded=True) as status:
        for i, (_, row) in enumerate(job_df.head(max_jobs).iterrows()):
            st.write(f"Job {i+1}/{max_jobs}: {row['headline'][:40]}...")
            
            job_text = f"Titel: {row['headline']}\nFöretag: {row['employer_name']}\nOmråde: {row['occupation_field']}\nBeskrivning: {row['description'][:800]}..."
            
            ai_result = analyze_job_with_gemini(job_text)
            if ai_result and (parsed := validate_gemini_response(ai_result)):
                results.append({**row.to_dict(), **parsed})
            else:
                st.warning(f"Failed to analyze: {row['headline'][:30]}...")
        
        status.update(label=f"✅ Completed! Analyzed {len(results)}/{max_jobs} jobs", state="complete")
    
    return results

def create_metrics(results):
    """Create metric cards - Extracted for reusability"""
    col1, col2, col3, col4 = st.columns(4)
    metrics = [
        ("Analyzed Jobs", len(results)),
        ("Senior Roles", sum(1 for r in results if 'Senior' in str(r.get('nivå', '')))),
        ("Remote Jobs", sum(1 for r in results if 'Remote' in str(r.get('arbetstyp', '')))),
        ("Python Jobs", sum(1 for r in results if any('Python' in str(s) for s in r.get('språk', []))))
    ]
    
    for col, (label, value) in zip([col1, col2, col3, col4], metrics):
        col.metric(label, value)

def create_skills_chart(results):
    """Create skills visualization - Separated for clarity"""
    all_skills = [skill for r in results for skill in (r.get('krav', []) + r.get('meriterande', []))]
    
    if not all_skills:
        st.info("No skills data to display")
        return
    
    skills_count = Counter(all_skills).most_common(15)
    fig = px.bar(
        x=[count for _, count in skills_count],
        y=[skill for skill, _ in skills_count],
        orientation='h',
        title="Most Demanded Skills",
        color=[count for _, count in skills_count],
        color_continuous_scale='viridis'
    )
    fig.update_layout(yaxis={'categoryorder': 'total ascending'}, height=600)
    st.plotly_chart(fig, use_container_width=True)

def create_linkedin_content(results):
    """Generate LinkedIn marketing content"""
    qualities = [q for r in results for q in r.get('kvaliteter', [])]
    
    if len(qualities) < 3:
        return
    
    qual_count = Counter(qualities).most_common(6)
    linkedin_post = f"""Hottest qualities in the job market:

1️⃣ {qual_count[0][0]} ({qual_count[0][1]} jobs)
2️⃣ {qual_count[1][0]} ({qual_count[1][1]} jobs)
3️⃣ {qual_count[2][0]} ({qual_count[2][1]} jobs)

#TalentAcquisition #JobSearch #HR #Skills #Career"""
    
    st.subheader("LinkedIn Marketing Content")
    st.code(linkedin_post, language="markdown")

def create_visualizations(results):
    """Main visualization function - Simplified"""
    if not results:
        st.warning("No data to display")
        return
    
    create_metrics(results)
    st.subheader("Analysis Results")
    create_skills_chart(results)
    create_linkedin_content(results)

def create_results_table(results):
    """Create and display results table with export functionality"""
    if not results:
        st.warning("No results to display")
        return
    
    # Transform data for display
    display_data = []
    for r in results:
        display_data.append({
            'Job Title': (r.get('headline', 'N/A')[:50] + '...' if len(r.get('headline', '')) > 50 else r.get('headline', 'N/A')),
            'Company': r.get('employer_name', 'N/A'),
            'Field': r.get('occupation_field', 'N/A'),
            'Level': r.get('nivå', 'N/A'),
            'Skills': ', '.join(r.get('krav', [])[:3]) + ('...' if len(r.get('krav', [])) > 3 else ''),
            'Languages': ', '.join(r.get('språk', [])[:3]),
            'Tools': ', '.join(r.get('verktyg', [])[:2]),
            'Work Type': r.get('arbetstyp', 'N/A'),
        })
    
    df = pd.DataFrame(display_data)
    st.dataframe(df, use_container_width=True)
    
    # Export section
    st.markdown("###Export Data")
    col1, col2 = st.columns(2)
    timestamp = pd.Timestamp.now().strftime('%Y%m%d_%H%M')
    
    with col1:
        st.download_button(
            "Download CSV",
            df.to_csv(index=False, encoding='utf-8'),
            f"skills_analysis_{timestamp}.csv",
            "text/csv", use_container_width=True
        )
    
    with col2:
        st.download_button(
            "Download JSON", 
            json.dumps(results, ensure_ascii=False, indent=2),
            f"detailed_analysis_{timestamp}.json",
            "application/json", use_container_width=True
        )

def main():
    """Streamlined main function"""
    st.title("AI Skills Analysis")
    st.markdown("*Quick AI analysis of job descriptions using Google Gemini*")
    
    # Sidebar setup
    with st.sidebar:
        st.header("Controls")
        
        # API Check
        if not (model := setup_gemini()):
            st.error("❌ API Setup Required")
            st.stop()
        st.success("✅ AI Ready")
        
        # Controls
        selected_field = st.selectbox("Job Field:", OCCUPATION_OPTIONS)
        max_jobs = st.slider("Jobs to Analyze:", 1, 15, 3)
        
        st.markdown("---")
        analyze_button = st.button("Start Analysis", type="primary", use_container_width=True)
        
        if 'results' in st.session_state:
            if st.button("Clear Results", type="secondary", use_container_width=True):
                del st.session_state['results']
                st.rerun()
    
    # Load and display data
    with st.spinner("Loading job data..."):
        job_data = load_job_data(selected_field, max_jobs)
    
    if job_data.empty:
        st.error("❌ No data found")
        st.stop()
    
    st.sidebar.info(f"{len(job_data)} jobs loaded")
    
    # Data preview
    with st.expander(f"Preview ({len(job_data)} jobs)", expanded=False):
        st.dataframe(job_data[['headline', 'employer_name', 'occupation_field']].head(), use_container_width=True)
    
    # Analysis
    if analyze_button:
        with st.spinner("Running AI analysis..."):
            results = analyze_jobs(job_data, max_jobs)
        
        if results:
            st.session_state['results'] = results
            st.success(f"Successfully analyzed {len(results)} jobs!")
            st.balloons() # Celebration effect
        else:
            st.error("❌ Analysis failed")
    
    # Display results
    if results := st.session_state.get('results'):
        st.markdown("---")
        st.subheader(f"Analysis Results ({len(results)} jobs)")
        
        tab1, tab2 = st.tabs(["Visualizations", "Data Table"])
        
        with tab1:
            create_visualizations(results)
        
        with tab2:
            create_results_table(results)
    else:
        st.info("Click 'Start Analysis' to begin")

if __name__ == "__main__":
    main()
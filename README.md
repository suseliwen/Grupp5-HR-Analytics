## HR Analytics Proof of Concept

### Project Overview

This project creates a data pipeline for an HR agency to automate the analysis of job advertisements from Arbetsförmedlingen. By transforming manual, time-consuming processes into an automated system, we enable talent acquisition specialists to strategically identify high-potential candidates, reduce administrative overhead, and significantly increase their capacity to match qualified talent with employer needs.

### Focus Areas

- Managers and business leaders (Chefer och verksamhetsledare)
- Professions with social focus (Yrken med social inriktning)
- Professions with technical focus (Yrken med teknisk inriktning)

### Technical Structure

- Data Collection: dlt to retrieve data from Jobtech API to DuckDB
- Data Transformation: dbt to structure data according to dimensional model
- Data Visualization: Streamlit dashboard for vacancy analysis
- Orchestration: Dagster for automated pipeline scheduling

### Installation

- Clone the repository from Github and add team members
- Install dependencies
- Configure dlt and dbt

### Run the Pipeline

- Extract data: python extraction/jobtech_api.py
- Transform data: dbt run
- Launch dashboard: streamlit run dashboard_app/jobads_dashboard.py

### Dashboard Features

KPI Metrics Dashboard - Real-time job market statistics
Geographic Analysis - Job distribution across Swedish counties
Trend Analysis - Historical recruitment patterns
AI Competency Analysis - Google Gemini extracts skills, requirements, and qualifications from job descriptions, visualizing top competencies and generating LinkedIn marketing content

### Collaboration Guidelines

- Work in feature branches with descriptive names
- Pull from main before creating pull requests
- Make small, focused commits
- Use the Kanban board to track progress

### Team Members

- Susanne
- Markus
- Roberto

### Sources

- [Jobtech API](https://jobsearch.api.jobtechdev.se/) - Swedish Public Employment Service API
- [Geographic Data](https://github.com/okfse/sweden-geojson) - Municipality and region mappings
- [Streamlit Documentation](https://docs.streamlit.io/) - Dashboard framework
- [Google Gemini API](https://ai.google.dev/gemini-api/docs) - AI language model

### Development Tools

- Version Control: Git & GitHub
- IDE: Visual Studio Code
- Database: DuckDB for analytics
- Orchestration: Dagster for pipeline
- Testing: dbt tests

### Future Applications

- Salary prediction models
- Predictive hiring trends
- Skills gap analysis

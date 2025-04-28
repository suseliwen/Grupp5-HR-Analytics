## HR Analytics Proof of Concept

### Project Overview

This project creates a data pipeline for an HR agency to automate the analysis of job advertisements from Arbetsförmedlingen. By transforming manual, time-consuming processes into an automated system, we enable talent acquisition specialists to strategically identify high-potential candidates, reduce administrative overhead, and significantly increase their capacity to match qualified talent with employer needs.

### Focus Areas Section

• Managers and business leaders
• Professions with social focus
• Professions with technical focus

### Technical Structure

• Data Collection: dlt to retrieve data from Jobtech API to DuckDB
• Data Transformation: dbt to structure data according to dimensional model
• Data Visualization: Streamlit dashboard for vacancy analysis

### Installation

• Clone the repository from Github and add team members
• Install dependencies
• Configure dlt and dbt

### Run the Pipeline

• Extract data: python extraction/jobtech_api.py
• Transform data: dbt run
• Launch dashboard: streamlit run dashboard/app.py

### Collaboration Guidelines

• Work in feature branches with descriptive names
• Pull from main before creating pull requests
• Make small, focused commits
• Use the Kanban board to track progress

### Team Members

• Susanne
• Markus
• Roberto

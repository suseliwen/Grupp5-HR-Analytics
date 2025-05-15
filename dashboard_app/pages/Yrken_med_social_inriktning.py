import streamlit as st
from utils import DataBase_Connection


st.set_page_config(page_title="HR Analytics Dashboard", layout="wide")
st.title("Yrkesområden med social inriktning")

st.markdown("Enligt Arbetsförmedlingen är yrken med social inriktning de som handlar om att hjälpa och stödja människor")
st.sidebar.header("Yrkesområden")

progress_bar = st.sidebar.progress(0)
status_text = st.sidebar.empty()


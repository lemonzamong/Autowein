import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import json

USER_API_URL = "http://localhost:8000"

st.set_page_config(page_title="Autowein's Digital Twin", layout="wide")

st.title("Autowein's Cognitive Digital Twin (ACDT)")
st.caption("Domain-Specific Market Insight Automation System")

# Sidebar - Configuration
st.sidebar.header("Control Panel")
domain = st.sidebar.selectbox("Domain", ["Mobility & EV", "Bio & Pharma", "Semiconductor"])
st.sidebar.info(f"Active Ontology: {domain}")

# Tabs
tab1, tab2, tab3 = st.tabs(["News Ingestion", "Graph Explorer", "Analyst Output"])

with tab1:
    st.header("1. Gatekeeper: News Selection")
    if st.button("Fetch Latest News"):
        with st.spinner("Scraping and Filtering..."):
            try:
                # Mock call or real call depending on API state
                # In real scenario: response = requests.post(f"{USER_API_URL}/ingest", json={"items": []})
                # For demo dashboard we simulate data if API is down
                 st.success("Fetched 3 relevant articles out of 50 crawled.")
                 st.dataframe(pd.DataFrame([
                     {"Title": "Canada imposes 100% tariff", "Source": "Reuters", "Score": 0.95},
                     {"Title": "Tesla FSD v12 Released", "Source": "TechCrunch", "Score": 0.88},
                     {"Title": "Rivian stocks plunge", "Source": "Bloomberg", "Score": 0.82}
                 ]))
            except Exception as e:
                st.error(f"API Error: {e}")

with tab2:
    st.header("2. Historian: Knowledge Graph")
    st.markdown("Visualizing the **Causal Chain** for the selected event.")
    
    # Hardcoded graph visualization for demo
    st.graphviz_chart('''
    digraph {
        rankdir=LR;
        node [shape=box style=filled fillcolor=lightblue];
        "USMCA (2020)" -> "Regional Value Content" [label="Mandates"];
        "Regional Value Content" -> "Canada Tariffs (2024)" [label="Justifies"];
        "Canada Tariffs (2024)" -> "Chinese EV Exclusion" [label="Causes"];
        "Chinese EV Exclusion" -> "Tesla Market Share" [label="Increases"];
    }
    ''')
    st.caption("Path extracted by GraphRAG Engine")

with tab3:
    st.header("3. Analyst: Daily Commentary")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Generated Insight")
        st.markdown("""
        ### Canada’s Tariff Move: A USMCA Checkmate
        
        **Summary**: Canada has aligned with the US by imposing a 100% surtax on Chinese EVs.
        
        **Analysis**: While this appears to be a sudden trade dispute, our **Historical Context** engine reveals it is a direct consequence of the **USMCA 2020** agreement's "unset clause" regarding non-market economies. 
        
        **Prediction**: This will likely force Chinese manufacturers like BYD to accelerate their factory plans in Mexico to bypass these tariffs, potentially triggering a 'backdoor' dispute by Q4 2025.
        """)
        
    with col2:
        st.subheader("Agent Reasoning")
        st.info("Planner: Found link to USMCA 2020.")
        st.info("Simulator: Ran counterfactual 'If no tariff -> Market flood'.")
        st.info("Critic: Style match 92%. Insight depth High.")
        
    if st.button("Approve & Publish"):
        st.balloons()
        st.success("Commentary published to Autowein.com")

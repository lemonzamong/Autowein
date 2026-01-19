import streamlit as st
import json
import os
from datetime import datetime
from glob import glob
import subprocess

st.set_page_config(page_title="Autowein Curator", layout="wide")

st.title("Autowein: Human-in-the-Loop Curator (Stage 2)")

# 1. Select Date
# Find all "1_selected.json" files
data_root = "data/daily"
dates = []
if os.path.exists(data_root):
    dates = sorted(os.listdir(data_root), reverse=True)

selected_date = st.selectbox("Select Date", dates)

if not selected_date:
    st.warning("No data found.")
    st.stop()
    
# 2. Load Data
# Try loading ranked version first
ranked_path = f"{data_root}/{selected_date}/1_selected_ranked.json"
legacy_path = f"{data_root}/{selected_date}/1_selected.json"

if os.path.exists(ranked_path):
    file_path = ranked_path
    data_type = "Ranked (LLM Included)"
else:
    file_path = legacy_path
    data_type = "Heuristic Only"
    
output_path = f"{data_root}/{selected_date}/2_curated.json"

if not os.path.exists(file_path):
    st.error(f"File not found: {file_path}")
    st.stop()

with open(file_path, "r", encoding="utf-8") as f:
    items = json.load(f)

st.info(f"Loaded {len(items)} items from Stage 1 ({data_type}).")

# 3. Selection UI
st.subheader("Select Top 10 Items")
st.caption("Please check the items you want to include in the Analysis Report.")

with st.form("selection_form"):
    selected_indices = []
    
    # Sort by score desc (LLM or Heuristic)
    items.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
    
    col1, col2 = st.columns([0.7, 0.3])
    
    for i, item in enumerate(items):
        score = item.get('relevance_score', 0)
        breakdown = item.get('scores_breakdown', {})
        
        # Breakdown String
        hybrid_info = ""
        llm_reason = ""
        if breakdown:
            base_str = f"TF: {breakdown.get('tfidf',0):.2f} | Sem: {breakdown.get('semantic',0):.2f}"
            if 'llm_score' in breakdown:
                hybrid_info = f" (🤖 LLM: {breakdown['llm_score']:.2f} | {base_str})"
                llm_reason = breakdown.get('llm_reason', '')
            else:
                hybrid_info = f" ({base_str} | Rep: {breakdown.get('reputation',0):.2f})"
        
        # Default select top 10
        default_val = i < 10
        
        # Highlight Low Reputation & Clusters
        rep_score = breakdown.get('reputation', 1.0) if breakdown else 1.0
        warning_icon = "⚠️" if rep_score < 0.8 else ""
        
        cluster_info = ""
        if hasattr(item, 'related_items') and item.related_items:
            cluster_info = f" (+{len(item.related_items)} related)"
        
        label = f"{warning_icon} [{score:.3f}] {item['title']}{cluster_info}"
        with st.expander(f"{label} {hybrid_info}", expanded=default_val):
            st.write(f"**Source:** {item.get('source')} | **Date:** {item.get('published_at')}")
            st.write(item.get('content', '')[:300] + "...")
            st.markdown(f"[Read Original]({item.get('url')})")
            
            # Checkbox inside expander might be tricky for form submission?
            # Better to put checkbox outside.
            
        checked = st.checkbox(f"Select #{i+1}", value=default_val, key=f"d_{i}")
        if checked:
            selected_indices.append(i)

    submitted = st.form_submit_button("Confirm Selection & Save")
    
    if submitted:
        curated_items = [items[i] for i in selected_indices]
        
        # Save
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(curated_items, f, indent=4, ensure_ascii=False)
            
        st.success(f"Saved {len(curated_items)} items to {output_path}")
        
        # 4. Trigger Automated Training (Active Learning)
        try:
            with st.spinner("🧠 Updating AI Reward Model based on your choices..."):
                # Dynamically import to avoid path issues if possible, or add to path
                import sys
                sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))
                from scripts.tools.train_irl import train_irl_head
                
                # Redirect stdout to capture training logs if needed, or just run it
                train_irl_head()
            st.success("✅ AI Model Updated! The system is now smarter.")
        except Exception as e:
            st.error(f"Training failed: {e}")

        # Trigger Analysis?
        st.write("Generating analysis report...")
        # In a real app we might run this async or in a separate process.
        # For now, just show the command to run.
        st.code(f"python3 scripts/pipeline/03_analysis.py", language="bash")
        

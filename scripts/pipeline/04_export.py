import sys
import os
import json
from datetime import datetime

# Add project root to path (scripts/pipeline/ -> ../../)
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from src.analyst.llm import GeminiClient, OpenAIClient

def get_mermaid_chart(client, content):
    prompt = f"""
    Based on the following analysis, generate a Mermaid JS Sequence Diagram code block 
    that visualizes the cause-and-effect relationship described.
    
    Analysis: {content[:1000]}...
    
    Output strictly the mermaid code inside a ```mermaid block.
    """
    try:
        return client.complete(prompt, "You are a Visualization Assistant.")
    except:
        return ""

def run_stage4():
    print("=== [Stage 4] Final Report Generation ===")
    
    # 1. Load Analyzed Data
    base_dir = "data/daily"
    if not os.path.exists(base_dir):
        print("No data found.")
        return
        
    dates = sorted(os.listdir(base_dir), reverse=True)
    today = dates[0]
    input_path = f"{base_dir}/{today}/3_analyzed.json"
    
    if not os.path.exists(input_path):
        print(f"Data not found: {input_path}")
        return
        
    with open(input_path, 'r') as f:
        data = json.load(f)
        
    print(f">>> Transforming {len(data)} analyses into final report...")
    
    # Initialize Viz LLM
    # Initialize Viz LLM
    gemini_key = os.getenv("GOOGLE_API_KEY", "AIzaSyDQX66EWC_ksMdMM2aLlbMImDLJvt6u-_I")
    if not gemini_key:
        print("Warning: GOOGLE_API_KEY not found. Visualization may fail.")
    viz_llm = GeminiClient(api_key=gemini_key) # Use Gemini for chart gen for speed/cost
    
    # 2. Format MD/HTML
    # Output File
    output_file = f"{base_dir}/{today}/4_report.md"
    
    with open(output_file, 'w') as f:
        f.write(f"# Autowein Daily Intelligence Report\n")
        f.write(f"**Date:** {today}\n\n")
        f.write(f"---\n\n")
        
        for i, item in enumerate(data):
            print(f"    > Generating Visualization for Item {i+1}...")
            mermaid_code = get_mermaid_chart(viz_llm, item['content'])
            
            f.write(f"## {item['title']}\n")
            
            # Metadata Badge
            conf = item.get('confidence_score', 0.0)
            hor = item.get('time_horizon', 'Unknown')
            f.write(f"> **Confidence**: {conf} | **Horizon**: {hor}\n\n")
            
            f.write(f"{item['content']}\n\n")
            
            # Visualization
            if "mermaid" in mermaid_code:
                f.write(f"### Visual Summary\n")
                f.write(f"{mermaid_code}\n\n")
            
            f.write(f"> **Reasoning Trace**:\n")
            for t in item['reasoning_trace']:
                f.write(f"> - {t}\n")
            f.write(f"\n---\n\n")
            
    print(f"=== [Stage 4] Complete. Report saved to {output_file} ===")

if __name__ == "__main__":
    run_stage4()

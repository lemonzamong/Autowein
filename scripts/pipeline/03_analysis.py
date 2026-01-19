import sys
import os
import json
from datetime import datetime
from typing import List, Dict

# Add project root to path
# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from src.core.config import ConfigLoader
from src.core.models import NewsItem, Commentary
from src.historian.engine import HistorianEngine
from src.historian.graph_db import Neo4jGraph
from src.analyst.engine import AnalystEngine
from dataclasses import asdict

def run_stage3():
    print("=== [Stage 3] Context Retrieval & Analysis ===")
    
    # 1. Determine Date & File Path
    # Default to today, or find latest '2_curated.json' folder?
    # For robust demo, let's look for the latest daily folder.
    base_dir = "data/daily"
    if not os.path.exists(base_dir):
        print("No data found.")
        return

    dates = sorted(os.listdir(base_dir), reverse=True)
    today = dates[0]
    date_dir = os.path.join(base_dir, today)
    input_path = os.path.join(date_dir, "2_curated.json")
    
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        print("Please run Stage 2 (Dashboard) and save items first.")
        return
        
    print(f">>> Loading Curated Data from {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    # Deserialization helper
    items = []
    for d in data:
        # Handle datetime parsing if strictly needed, or let Pydantic/dataclass handle if used
        # NewsItem is a dataclass, so we can unpack. 
        # But 'published_at' is likely a string in JSON.
        if 'published_at' in d and isinstance(d['published_at'], str):
             try:
                 d['published_at'] = datetime.fromisoformat(d['published_at'])
             except:
                 pass # Keep as string or simplified
                 
        # Re-construct object manually or via simple mapping for now
        # Ideally: item = NewsItem(**d) but nested fields might fail
        # Quick hack: Just keep dictionary for Analyst context if models aren't strict,
        # OR robustly reconstruct. Let's try robust reconstruction.
        item = NewsItem(
            id=d.get('id'),
            title=d.get('title'),
            url=d.get('url'),
            source=d.get('source'),
            published_at=d.get('published_at'),
            content=d.get('content'),
            relevance_score=d.get('relevance_score', 0.0),
            scores_breakdown=d.get('scores_breakdown', {}),
            related_items=d.get('related_items', [])
        )
        items.append(item)
        
    print(f">>> Processing {len(items)} items...")
    
    # 2. Initialize Engines
    # Historian: Needs Graph DB
    graph = Neo4jGraph() # Will check env vars or default
    historian = HistorianEngine(graph_db=graph)
    
    # Analyst: Check for Keys via Config
    loader = ConfigLoader("config/mobility.yaml")
    config = loader.load()
    
    gemini_key = config.api_keys.get('google_gemini') or os.getenv("GOOGLE_API_KEY")
    api_key = config.api_keys.get('openai') or os.getenv("OPENAI_API_KEY")
    
    use_gemini = True
    use_openai = False
    
    if use_gemini and gemini_key:
        print(f">>> Initializing Analyst with Google Gemini (Key Provided)...")
        active_key = gemini_key
    elif api_key:
        print(f">>> Initializing Analyst with OpenAI (Key Found)...")
        use_openai = True
        active_key = api_key
    else:
        print(f">>> Initializing Analyst with Mock LLM (No Key)...")
        active_key = None
        
    analyst = AnalystEngine(use_openai=use_openai, use_gemini=use_gemini, api_key=active_key)
    
    commentaries = []
    
    # 3. Processing Loop
    for i, item in enumerate(items):
        print(f"\n[{i+1}/{len(items)}] Analyzing: {item.title[:50]}...")
        
        # A. Retrieve Context
        try:
            print("    > Querying Knowledge Graph...")
            context = historian.retrieve_context(item)
            events = context.get('related_events', [])
            print(f"    > Found {len(events)} related historical events.")
            
            # [NEW] Add Related News from Clustering
            related_news = []
            if hasattr(item, 'related_items') and item.related_items:
                # Convert related items to simplified dicts
                for r in item.related_items:
                    # Depending on how it's stored (obj or dict), handle safely
                    r_title = r.title if hasattr(r, 'title') else r.get('title')
                    r_source = r.source if hasattr(r, 'source') else r.get('source')
                    if r_title:
                        related_news.append(f"- {r_title} ({r_source})")
                        
            context['related_news'] = related_news
            if related_news:
                print(f"    > Integrated {len(related_news)} similar reports into context.")
            
        except Exception as e:
            print(f"    > Historian Error: {e}")
            context = {"related_events": [], "related_news": []}
            
        # B. Generate Analysis
        try:
            print("    > Generating Commentary (Agentic Workflow)...")
            commentary = analyst.generate_commentary(item, context_data=context)
            commentaries.append(commentary)
            print(f"    > Done. Title: {commentary.title}")
        except Exception as e:
            print(f"    > Analyst Error: {e}")
            
    # 4. Save Results
    output_path = os.path.join(date_dir, "3_analyzed.json")
    
    class DateTimeEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, datetime):
                return o.isoformat()
            return super().default(o)

    outputs = [asdict(c) for c in commentaries]
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(outputs, f, indent=4, ensure_ascii=False, cls=DateTimeEncoder)
        
    print(f"\n=== [Stage 3] Complete. Saved {len(outputs)} reports to {output_path} ===")
    
    # Cleanup
    if hasattr(graph, 'close'):
        graph.close()

if __name__ == "__main__":
    run_stage3()

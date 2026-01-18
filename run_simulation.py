from datetime import datetime
from src.core.models import NewsItem, Event, Entity, EntityType
from src.core.config import ConfigLoader
from src.gatekeeper.engine import GatekeeperEngine
from src.historian.graph_db import LocalGraph
from src.historian.engine import HistorianEngine
from src.analyst.engine import AnalystEngine
from src.editor.engine import EditorEngine

def run_demo():
    print("=== Autowein's Cognitive Digital Twin (ACDT) Simulation ===\n")
    
    # 1. Initialize
    print("[Init] Loading Configuration...")
    config = ConfigLoader("config_mobility.yaml").load()
    
    graph = LocalGraph()
    gatekeeper = GatekeeperEngine(config)
    historian = HistorianEngine(graph)
    analyst = AnalystEngine()
    editor = EditorEngine()
    
    # 2. Populate History (The Knowledge Graph)
    print("\n[Historian] Populating 10-year History Graph...")
    usmca_event = Event(
        id="EVT_2020_USMCA",
        date=datetime(2020, 7, 1),
        description="USMCA agreement enters into force, requiring higher regional value content for autos.",
        entities=["US", "Canada", "Mexico"],
        event_type="Trade_Agreement",
        impact_score=0.9
    )
    graph.add_event(usmca_event)
    print(f" -> Added Event: {usmca_event.description}")
    
    # 3. Ingest Today's News (Load from Crawler Output)
    import json
    import os
    
    CORPUS_FILE = "data/autowein_full_corpus.jsonl"
    raw_news = []
    
    if os.path.exists(CORPUS_FILE) and os.path.getsize(CORPUS_FILE) > 0:
        print(f"\n[Gatekeeper] Loading REAL news from {CORPUS_FILE}...")
        with open(CORPUS_FILE, 'r') as f:
            # Read last 5 items
            lines = f.readlines()[-5:]
            for line in lines:
                try:
                    data = json.loads(line)
                    raw_news.append(NewsItem(
                        id=data.get('id', 'Unknown'),
                        title=data.get('title', 'No Title'),
                        content=data.get('text', '')[:500] + "...", # Truncate for display
                        url=data.get('url', ''),
                        published_at=datetime.now(),
                        source="Autowein Crawler"
                    ))
                except: pass
    else:
        print("\n[Gatekeeper] No crawled data found. Using Mock Data.")
        raw_news = [
            NewsItem(id="MOCK_1", title="Mock Data", content="Mock Content", url="http://mock", published_at=datetime.now(), source="Mock")
        ]
    
    selected_news = gatekeeper.select_news(raw_news)
    print(f" -> Selected {len(selected_news)} items from recent crawler output.")
    if not selected_news:
        print(" -> No relevant news found in batch.")
        return
        
    target_news = selected_news[0]
    print(f" -> Target: {target_news.title}")
    
    # 4. Context Retrieval
    print("\n[Historian] Retrieving Context...")
    context = historian.retrieve_context(target_news)
    print(f" -> Found related events: {[e.id for e in context['related_events']]}")
    print(f" -> Trace: {context['path_trace']}")
    
    # 5. Analysis & Simulation
    print("\n[Analyst] Generating Commentary...")
    commentary = analyst.generate_commentary(target_news, context)
    
    print("\n" + "="*50)
    print(f"TITLE: {commentary.title}")
    print("="*50)
    print(f"{commentary.content}")
    print("="*50)
    print("AGENTS' THOUGHTS:")
    for trace in commentary.reasoning_trace:
        print(f"- {trace}")
    print(f"- Counterfactual: {commentary.counterfactuals[0]}")
    
    # 6. Review
    print("\n[Editor] reviewing...")
    passed = editor.review_commentary(commentary)
    print(f" -> Editor Score: {commentary.style_score} (Passed: {passed})")

if __name__ == "__main__":
    run_demo()

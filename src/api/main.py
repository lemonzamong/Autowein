from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

from src.core.config import ConfigLoader
from src.core.models import NewsItem, Commentary, Event
from src.gatekeeper.engine import GatekeeperEngine
from src.historian.graph_db import LocalGraph
from src.historian.engine import HistorianEngine
from src.analyst.engine import AnalystEngine
from src.editor.engine import EditorEngine

app = FastAPI(title="Autowein's Cognitive Digital Twin API")

# Initialize Singletons
config = ConfigLoader("config_mobility.yaml").load()

# 1. Historian: Try Neo4j, fallback to Local
try:
    from src.historian.graph_db import Neo4jGraph
    # In production, credentials should come from env vars
    # For now, we wrap in try/except to fallback if Neo4j is not running
    graph_db = Neo4jGraph(uri="bolt://localhost:7687", user="neo4j", password="password")
    print(" [System] Connected to Neo4j Production Database.")
except Exception as e:
    print(f" [System] Neo4j connection failed ({e}). Falling back to LocalGraph (Memory).")
    graph_db = LocalGraph()

gatekeeper = GatekeeperEngine(config)
historian = HistorianEngine(graph_db)

# 2. Analyst: Try OpenAI, fallback to Mock
# OpenAIClient checks ENV inside its init, so we just instantiate.
# If no key, it might error on call, or we can check here.
import os
use_openai = bool(os.getenv("OPENAI_API_KEY"))
analyst = AnalystEngine(use_openai=use_openai)
print(f" [System] Analyst Agent initialized (Use OpenAI: {use_openai}).")

editor = EditorEngine()

# In-memory storage for demo
news_store: Dict[str, NewsItem] = {}

class IngestRequest(BaseModel):
    items: List[NewsItem]

class AnalysisResponse(BaseModel):
    news_id: str
    commentary: Commentary
    context: Dict[str, Any]

@app.post("/ingest", response_model=List[NewsItem])
def ingest_news(request: IngestRequest):
    """
    Ingests news items, filters them via Gatekeeper, and stores relevant ones.
    """
    selected = gatekeeper.select_news(request.items)
    
    for item in selected:
        news_store[item.id] = item
        # In a real system, we would extract events here and add to graph
        # For demo, we assume the graph is pre-populated or populated separately
        
    return selected

@app.post("/analyze/{news_id}", response_model=AnalysisResponse)
def analyze_news(news_id: str):
    """
    Generates commentary for a specific news item.
    """
    if news_id not in news_store:
        raise HTTPException(status_code=404, detail="News item not found")
        
    item = news_store[news_id]
    
    # 1. Retrieve Context
    context = historian.retrieve_context(item)
    
    # 2. Generate Commentary
    commentary = analyst.generate_commentary(item, context)
    
    # 3. Review (Editor)
    passed = editor.review_commentary(commentary)
    
    # If failed, we would loop back. For now, we return heavily annotated commentary.
    if not passed:
        commentary.content += "\n\n[EDITOR NOTE: This draft needs revision.]"
        
    return AnalysisResponse(
        news_id=news_id,
        commentary=commentary,
        context=context
    )

# Debug endpoint to populate graph
@app.post("/debug/add_event")
def add_event(event: Event):
    graph_db.add_event(event)
    return {"status": "success"}

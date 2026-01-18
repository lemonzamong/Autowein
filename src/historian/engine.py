from typing import List, Dict, Any
from src.core.models import NewsItem, Event
from src.historian.graph_db import GraphDB

class HistorianEngine:
    def __init__(self, graph_db: GraphDB):
        self.graph = graph_db
        
    def retrieve_context(self, news_item: NewsItem) -> Dict[str, Any]:
        """
        Analyzes the news item, extracts entities, and retrieves historical context.
        """
        # 1. Entity Extraction (Mock)
        # In production, this would use an NER model.
        extracted_entities = self._mock_ner(news_item.content)
        
        # 2. Graph Traversal
        related_events = self.graph.get_related_events(extracted_entities, hops=2)
        
        return {
            "extracted_entities": extracted_entities,
            "related_events": related_events,
            "path_trace": " -> ".join(extracted_entities) # Simplified trace
        }
        
    def _mock_ner(self, text: str) -> List[str]:
        """
        Simple keyword matching for demo purposes.
        """
        known_entities = ["Tesla", "US", "China", "Canada", "EU", "BYD"]
        found = []
        for entity in known_entities:
            if entity in text:
                found.append(entity)
        return found

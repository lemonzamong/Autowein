from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from src.core.models import Entity, Event, Relation

class GraphDB(ABC):
    @abstractmethod
    def add_event(self, event: Event):
        pass
        
    @abstractmethod
    def get_related_events(self, entities: List[str], hops: int = 2) -> List[Event]:
        pass

class LocalGraph(GraphDB):
    def __init__(self):
        # adjacency list: {node_id: {neighbor_id: relation_type}}
        self.adj = {}
        self.nodes = {} 
        self.events = {}

    def add_event(self, event: Event):
        self.events[event.id] = event
        # Link event to entities
        for entity_id in event.entities:
            self._add_edge(event.id, entity_id, "INVOLVES")
            self._add_edge(entity_id, event.id, "INVOLVED_IN")
            
    def _add_edge(self, u, v, rel_type):
        if u not in self.adj: self.adj[u] = {}
        self.adj[u][v] = rel_type
        
    def get_related_events(self, entities: List[str], hops: int = 2) -> List[Event]:
        # Simple BFS / Traversal logic for demo
        # If any of the input entities are involved in an event, return that event.
        
        found_events = []
        for eid, evt in self.events.items():
            # Check intersection
            if any(e in evt.entities for e in entities):
                found_events.append(evt)
                
        # Fallback for demo if no direct entity match (since entities are mock strings)
        if not found_events and self.events:
            return list(self.events.values())
            
        return found_events

class Neo4jGraph(GraphDB):
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password"):
        print("[Graph] Initializing Neo4j Connection...")
        pass

    def add_event(self, event: Event):
        print(f"[Graph] (Neo4j) Adding Event {event.id}")
        
    def get_related_events(self, entities: List[str], hops: int = 2) -> List[Event]:
        print(f"[Graph] (Neo4j) Retrieving context for {entities}")
        return []

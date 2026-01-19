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
    def __init__(self, uri=None, user=None, password=None):
        import os
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "password")
        
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            print(f"[Graph] Connected to Neo4j at {self.uri}")
        except ImportError:
            print("[Graph] Neo4j Driver not installed. Run 'pip install neo4j'.")
            self.driver = None
        except Exception as e:
            print(f"[Graph] Connection Failed: {e}")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def add_event(self, event: Event):
        if not self.driver: return
        
        query = """
        MERGE (e:Event {id: $event_id})
        SET e.title = $title, e.date = $date, e.impact_score = $impact
        WITH e
        UNWIND $entities as entity_name
        MERGE (n:Entity {name: entity_name})
        MERGE (n)-[:INVOLVED_IN]->(e)
        """
        
        try:
            with self.driver.session() as session:
                session.run(query, 
                            event_id=event.id, 
                            title=event.title or "Unknown Event",
                            date=event.timestamp.isoformat() if event.timestamp else "",
                            impact=event.impact_score,
                            entities=event.entities)
            print(f"[Graph] Added Event {event.id} to Neo4j")
        except Exception as ex:
            print(f"[Graph] Error adding event: {ex}")

    def get_related_events(self, entities: List[str], hops: int = 2) -> List[Event]:
        if not self.driver: return []
        
        # Cypher: Find events connected to these entities within N hops
        # Cypher: 2-Hop Impact Analysis (Graph-RAG)
        # Finds events related to the target entities, or related to PARTNERS of the target entities.
        query = """
        MATCH (target:Entity)-[:INVOLVES|INVOLVED_IN|RELATED_TO*1..2]-(e:Event)
        WHERE target.name IN $entities
        AND e.date > '2020-01-01'  // Filter for relevance (optional, can be dynamic)
        RETURN DISTINCT e.id as id, e.title as title, e.date as date, e.impact_score as impact
        ORDER BY e.impact_score DESC
        LIMIT 5
        """
        
        results = []
        try:
            with self.driver.session() as session:
                records = session.run(query, entities=entities)
                for record in records:
                    # Reconstruct Event object (simplified)
                    evt = Event(
                        id=record['id'],
                        title=record['title'],
                        content="Retrieved from Graph",
                        entities=[], # Simplified
                        timestamp=None # Parsing logic skipped for brevity
                    )
                    results.append(evt)
        except Exception as ex:
            print(f"[Graph] Error retrieving events: {ex}")
            
        print(f"[Graph] Retrieved {len(results)} related events from Neo4j")
        return results

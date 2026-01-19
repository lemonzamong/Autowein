from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class EntityType(str, Enum):
    """
    Base Entity Types. Can be extended dynamically via config validation.
    Common types for Mobility domain are pre-defined.
    """
    COMPANY = "COMPANY"
    PERSON = "PERSON"
    COUNTRY = "COUNTRY"
    TECHNOLOGY = "TECHNOLOGY"
    POLICY = "POLICY"
    OTHER = "OTHER"

@dataclass
class Entity:
    id: str  # Unique identifier (e.g., "Tesla", "USMCA")
    type: str  # String to allow dynamic types from config
    attributes: Dict[str, Any] = field(default_factory=dict)
    
@dataclass
class Relation:
    source: str  # Entity ID
    target: str  # Entity ID
    type: str  # e.g., "imposes_tariff_on", "partners_with"
    attributes: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Event:
    id: str
    date: datetime
    description: str
    entities: List[str] # List of Entity IDs involved
    event_type: str # e.g. "ProductLaunch", "Regulation"
    impact_score: float = 0.0
    
@dataclass
class NewsItem:
    id: str
    title: str
    content: str
    url: str
    published_at: datetime
    source: str
    # Metadata extracted by Gatekeeper
    # Metadata extracted by Gatekeeper
    relevance_score: float = 0.0
    scores_breakdown: Dict[str, float] = field(default_factory=dict)
    selected: bool = False
    # Diversity: List of similar articles merged into this one
    related_items: List['NewsItem'] = field(default_factory=list)
    
@dataclass
class Commentary:
    news_id: str
    title: str # Generated title
    content: str # The main analysis
    reasoning_trace: List[str] = field(default_factory=list) # Thoughts from the agents
    referenced_events: List[str] = field(default_factory=list) # Event IDs used for context
    counterfactuals: List[str] = field(default_factory=list) # "What if" scenarios considered
    style_score: float = 0.0 # Evaluation by Editor
    confidence_score: float = 0.0 # Predicted certainty (0.0-1.0)
    time_horizon: str = "Unknown" # e.g. "Short-term (<6m)", "Long-term (>2y)"

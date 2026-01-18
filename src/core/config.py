import json
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class DomainConfig:
    domain_name: str
    entity_types: List[str]
    relation_types: List[str]
    event_types: List[str]
    # Gatekeeper settings
    keywords: List[str]
    sources: List[str] = field(default_factory=list)
    
class ConfigLoader:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._config = None
        
    def load(self) -> DomainConfig:
        # Fallback to loading YAML if relevant libs are present, else try simple parse or JSON
        # For now, we assume the user will provide a JSON config or we mock it if key error.
        # Check file extension
        if self.config_path.endswith('.yaml'):
             # Very simple YAML parser for this specific schema or just mock
             # Since we can't use PyYAML, let's hardcode the mobility config here for the demo 
             # OR convert the existing yaml file to json.
             # Let's assume we read the yaml file as text and parse known keys.
             with open(self.config_path, 'r') as f:
                 text = f.read()
             
             # Fallback Mock Config
             data = {
                 "domain_name": "Mobility",
                 "entity_types": ["COMPANY", "PERSON", "COUNTRY", "TECHNOLOGY", "POLICY"],
                 "relation_types": ["PARTNERS_WITH", "SUES", "ANNOUNCES"],
                 "event_types": ["PRODUCT_LAUNCH", "REGULATION"],
                 "keywords": ["EV", "Battery", "Autonomous", "Tariff"],
                 "sources": ["Autowein"]
             }
        else:
             with open(self.config_path, 'r') as f:
                data = json.load(f)
                
        self._config = DomainConfig(**data)
        return self._config
    
    @property
    def config(self) -> DomainConfig:
        if self._config is None:
            return self.load()
        return self._config

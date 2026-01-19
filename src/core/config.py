import json
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class DomainConfig:
    domain_name: str
    sources: List[str] = field(default_factory=list)
    # Legacy fields (kept for compatibility but unused)
    entity_types: List[str] = field(default_factory=list)
    relation_types: List[str] = field(default_factory=list)
    event_types: List[str] = field(default_factory=list)
    weighted_keywords: Dict[str, float] = field(default_factory=dict)
    
class ConfigLoader:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._config = None
        
    def load(self) -> DomainConfig:
        import re
        
        # Default empty config structure
        data = {
            "domain_name": "Mobility",
            "sources": []
        }
        
        if self.config_path.endswith('.yaml'):
             try:
                 with open(self.config_path, 'r', encoding='utf-8') as f:
                     text = f.read()
                     
                 # Parse Sources (List)
                 # Capture from "sources:" until the next line that starts with a character (no indentation)
                 src_block_match = re.search(r'sources:\s*\n((?:(?:\s+|-|#).*\n?)+)', text)
                 if src_block_match:
                     block = src_block_match.group(1)
                     # Find - "URL" or - 'URL'
                     matches = re.findall(r'-\s+[\'"](.*?)[\'"]', block)
                     if matches:
                        data["sources"] = matches
                     
             except Exception as e:
                 print(f"[Config] Error parsing YAML: {e}. Using defaults.")

        else:
             with open(self.config_path, 'r') as f:
                data = json.load(f)
                
        self._config = DomainConfig(
            domain_name=data.get('domain_name', 'Mobility & EV'),
            sources=data.get('sources', [])
        )
        return self._config
    
    @property
    def config(self) -> DomainConfig:
        if self._config is None:
            return self.load()
        return self._config

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
    weighted_keywords: Dict[str, float]
    sources: List[str] = field(default_factory=list)
    
class ConfigLoader:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._config = None
        
    def load(self) -> DomainConfig:
        import re
        
        # Default empty config structure
        data = {
            "domain_name": "Mobility",
            "entity_types": [],
            "relation_types": [],
            "event_types": [],
            "weighted_keywords": {},
            "sources": []
        }
        
        if self.config_path.endswith('.yaml'):
             try:
                 with open(self.config_path, 'r', encoding='utf-8') as f:
                     text = f.read()
                     
                 # 1. Parse Weighted Keywords (Dict)
                 # Looks for: "KEY": VALUE
                 # We capture lines inside weighted_keywords block roughly
                 wk_block_match = re.search(r'weighted_keywords:\s*\n((?:\s+.*?\n)+)', text)
                 if wk_block_match:
                     block = wk_block_match.group(1)
                     # Find "Key": Value
                     matches = re.findall(r'[\'"](.*?)[\'"]:\s*([\d\.]+)', block)
                     for k, v in matches:
                         data["weighted_keywords"][k] = float(v)
                         
                 # 2. Parse Sources (List)
                 # Capture from "sources:" until the next line that starts with a character (no indentation)
                 # or End of File.
                 # The 'sources:' line itself is already found? No, we search for it.
                 # We want to match `sources:\n` followed by indented content.
                 
                 # Pattern: sources: (anything indented or blank or comments) until (start of line alphanumeric)
                 # Actually, simpler: just find "sources:" and then grab lines that start with whitespace -
                 
                 src_block_match = re.search(r'sources:\s*\n((?:(?:\s+|-|#).*\n?)+)', text)
                 if src_block_match:
                     block = src_block_match.group(1)
                     # Find - "URL" or - 'URL'
                     # Mocks typical yaml list item: - "value"
                     matches = re.findall(r'-\s+[\'"](.*?)[\'"]', block)
                     if matches:
                        data["sources"] = matches
                     
             except Exception as e:
                 print(f"[Config] Error parsing YAML: {e}. Using defaults.")

        else:
             with open(self.config_path, 'r') as f:
                data = json.load(f)
                
        self._config = DomainConfig(
            domain_name=data.get('domain_name', 'Unknown'),
            entity_types=data.get('entity_types', []),
            relation_types=data.get('relation_types', []),
            event_types=data.get('event_types', []),
            weighted_keywords=data.get('weighted_keywords', {}), 
            sources=data.get('sources', [])
        )
        return self._config
    
    @property
    def config(self) -> DomainConfig:
        if self._config is None:
            return self.load()
        return self._config

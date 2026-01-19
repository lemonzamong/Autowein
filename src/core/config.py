import json
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class DomainConfig:
    domain_name: str
    sources: List[str] = field(default_factory=list)
    # Reputation settings
    # Reputation settings
    trust_list: List[str] = field(default_factory=list)
    block_list: List[str] = field(default_factory=list)
    
    # API Keys
    api_keys: Dict[str, str] = field(default_factory=dict)
    
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
        import yaml # Try to use yaml if available, else fallback to regex
        
        # Default empty config structure
        data = {
            "domain_name": "Mobility",
            "sources": [],
            "trust_list": [],
            "block_list": [],
            "api_keys": {}
        }
        
        if self.config_path.endswith('.yaml'):
             try:
                 import yaml
                 with open(self.config_path, 'r', encoding='utf-8') as f:
                     parsed = yaml.safe_load(f)
                 
                 # Mapped directly from YAML structure
                 if parsed:
                     data['domain_name'] = parsed.get('domain_name', data['domain_name'])
                     data['sources'] = parsed.get('sources', [])
                     data['api_keys'] = parsed.get('api_keys', {})
                     
                     rep = parsed.get('reputation', {})
                     data['trust_list'] = rep.get('trust_list', [])
                     data['block_list'] = rep.get('block_list', [])
                     
                     # Check for legacy root-level keys if reputation dict is missing
                     if not data['trust_list'] and 'trust_list' in parsed:
                         data['trust_list'] = parsed['trust_list']
                     if not data['block_list'] and 'block_list' in parsed:
                         data['block_list'] = parsed['block_list']

             except ImportError:
                 print("[Config] Error: PyYAML not installed. Please run `pip install pyyaml`.")
                 # Fallback to crude regex if absolutely necessary, or just fail safely
                 pass
             except Exception as e:
                 print(f"[Config] Error parsing YAML: {e}. Using defaults.")

        else:
             with open(self.config_path, 'r') as f:
                data = json.load(f)
                
        self._config = DomainConfig(
            domain_name=data.get('domain_name', 'Mobility & EV'),
            sources=data.get('sources', []),
            trust_list=data.get('trust_list', []),
            block_list=data.get('block_list', []),
            api_keys=data.get('api_keys', {})
        )
        return self._config
    
    @property
    def config(self) -> DomainConfig:
        if self._config is None:
            return self.load()
        return self._config

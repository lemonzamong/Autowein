from typing import List
from src.core.models import NewsItem
from src.core.config import DomainConfig
from src.gatekeeper.scraper import RealScraper

class GatekeeperEngine:
    def __init__(self, config: DomainConfig):
        self.config = config
        self.scraper = RealScraper(sources=config.sources)
        
    def fetch_and_select(self) -> List[NewsItem]:
        """
        Fetches live news and filters it.
        """
        raw_news = self.scraper.fetch_news(None, None)
        return self.select_news(raw_news)

    def select_news(self, news_items: List[NewsItem]) -> List[NewsItem]:
        """
        Filters and scores news items based on domain configuration.
        """
        selected_items = []
        
        for item in news_items:
            score = self._calculate_score(item)
            item.relevance_score = score
            
            # Simple threshold for MVP. Ideally this matches the top N items.
            if score > 0.5:
                item.selected = True
                selected_items.append(item)
                
        return selected_items
    
    def _calculate_score(self, item: NewsItem) -> float:
        """
        Calculates relevance score based on keyword matching.
        Simulates the 'Impact Scorer' mentioned in the spec.
        """
        score = 0.0
        content_lower = (item.title + " " + item.content).lower()
        
        # 1. Keyword Matching
        matched_keywords = 0
        for keyword in self.config.keywords:
            if keyword.lower() in content_lower:
                matched_keywords += 1
                
        if matched_keywords > 0:
            score += 0.5 + (matched_keywords * 0.1)
            
        # 2. Heuristics (e.g. source credibility, length) - skipped for MVP
        
        return min(score, 1.0) # Cap at 1.0

import urllib.request
import re
from datetime import datetime
from typing import List, Optional
from src.core.models import NewsItem

class BaseScraper:
    def scrape(self) -> List[NewsItem]:
        raise NotImplementedError

class RealScraper(BaseScraper):
    def __init__(self, sources: List[str] = None):
        self.sources = sources or ["https://autowein.com"]
        
    def scrape(self) -> List[NewsItem]:
        print(f"[Scraper] Fetching from {self.sources}...")
        news_items = []
        for url in self.sources:
            try:
                # Standard lib only
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    html = response.read().decode('utf-8')
                
                # Simple Regex Regex for titles (H2/H3/A) to avoid BS4 dependency
                # e.g. <h2 class="entry-title"><a href="...">Title</a></h2>
                matches = re.findall(r'<h[23][^>]*><a[^>]*href=["\'](.*?)["\'][^>]*>(.*?)</a></h[23]>', html)
                
                for i, (link, title) in enumerate(matches[:5]):
                    # Clean title
                    title = re.sub(r'<[^>]+>', '', title).strip()
                    
                    news_items.append(NewsItem(
                        id=f"SCRAPED_{i}",
                        title=title,
                        content=f"Snippet: {title}...",
                        url=link,
                        published_at=datetime.now(),
                        source=url
                    ))
            except Exception as e:
                print(f"[Scraper] Error scraping {url}: {e}")
                
        return news_items

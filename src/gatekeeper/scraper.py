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
        print(f"[Scraper] Fetching from {len(self.sources)} sources...")
        news_items = []
        for url in self.sources:
            try:
                # Safe Encode URL for non-ASCII characters
                # include + in safe to prevent breaking query parameters (space)
                import urllib.parse
                safe_url = urllib.parse.quote(url, safe=':/?&=+')
                
                # Standard lib fetch
                # Use curl user-agent as it proved successful in CLI
                req = urllib.request.Request(safe_url, headers={'User-Agent': 'curl/7.68.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    content = response.read()

                # Detect RSS/XML
                if b'<rss' in content or b'<feed' in content:
                    news_items.extend(self._parse_rss(content, url))
                else:
                    # Fallback RegEx for HTML
                    # Debug: if it's short, print it
                    if len(content) < 2000:
                         print(f"[Scraper] Short content from {url}: {content[:200]}")
                    
                    html = content.decode('utf-8', errors='ignore')
                    matches = re.findall(r'<h[23][^>]*><a[^>]*href=["\'](.*?)["\'][^>]*>(.*?)</a></h[23]>', html)
                    for i, (link, title) in enumerate(matches[:500]):
                        title = re.sub(r'<[^>]+>', '', title).strip()
                        news_items.append(NewsItem(
                            id=f"SCRAPED_{len(news_items)}",
                            title=title,
                            content=f"Snippet: {title}...",
                            url=link if link.startswith('http') else url + link,
                            published_at=datetime.now(),
                            source=url
                        ))
                        
            except Exception as e:
                print(f"[Scraper] Error scraping {url}: {e}")
                
        return news_items

    def _parse_rss(self, content: bytes, source_url: str) -> List[NewsItem]:
        items = []
        try:
            # Debug: Print first 100 bytes to verify content
            # print(f"[Scraper] Parsing {len(content)} bytes from {source_url}")
            # print(f"[Scraper] Head: {content[:100]}") 

            import xml.etree.ElementTree as ET
            # Parse XML
            root = ET.fromstring(content)
            # print(f"[Scraper] Root Tag: {root.tag}")
            
            # RSS 2.0 uses <channel><item>...
            # Atom uses <entry>...
            
            count = 0 
            # RSS namespace handling? usually not needed for basic item tag unless strict
            items_found = root.findall('.//item') + root.findall('.//entry') + root.findall('.//{http://purl.org/rss/1.0/}item')
            # print(f"[Scraper] Found {len(items_found)} raw items")

            for item in items_found:
                # Removed limit as per user request
                # if count >= 50: break 

                
                title = item.find('title')
                link = item.find('link')
                desc = item.find('description') or item.find('summary')
                
                title_text = title.text.strip() if title is not None and title.text else "No Title"
                # Atom link usually has href attr, RSS has text
                link_text = link.text.strip() if link is not None and link.text else (link.get('href') if link is not None else "")
                desc_text = desc.text.strip() if desc is not None and desc.text else ""
                
                # Remove HTML from desc
                desc_text = re.sub(r'<[^>]+>', '', desc_text)[:200] + "..."

                # Parse Date
                pub_date_str = item.find('pubDate')
                pub_date = datetime.now()
                if pub_date_str is not None and pub_date_str.text:
                    try:
                        from email.utils import parsedate_to_datetime
                        # Returns offset-aware datetime
                        pub_date = parsedate_to_datetime(pub_date_str.text)
                        # Remove timezone for simpler comparison if needed, or keep it. 
                        # Let's keep it but ensure we handle it later.
                    except:
                        pass
                elif item.find('updated') is not None:
                     # Atom uses 'updated' and ISO format
                     try:
                         pub_date = datetime.fromisoformat(item.find('updated').text.replace('Z', '+00:00'))
                     except: pass

                items.append(NewsItem(
                    id=f"RSS_{source_url}_{count}",
                    title=title_text,
                    content=str(title_text + " " + desc_text), 
                    url=link_text,
                    published_at=pub_date,
                    source=source_url,
                    # [NEW] Extracted Metadata
                    author=self._get_text(item, ['creator', 'author', 'dc:creator']),
                    tags=[c.text for c in item.findall('category') if c.text],
                    image_url=self._get_image(item)
                ))
                count += 1
                
            print(f"[Scraper] Parsed {len(items)} items from RSS: {source_url}")
        except Exception as e:
            print(f"[Scraper] RSS Parse Error: {e}")
            
        return items

    def _get_text(self, item, tags):
        for tag in tags:
            # Try finding with namespace wildcard roughly or exact match
            # Python ElementTree namespace handling is tricky.
            # We try direct match first.
            res = item.find(tag)
            if res is not None and res.text:
                return res.text
            # Try iterate children if namespace issues
            for child in item:
                if any(t in child.tag for t in tags):
                    return child.text
        return "Unknown"

    def _get_image(self, item):
        # Media Content / Enclosure
        # Check <enclosure url="...">
        enc = item.find('enclosure')
        if enc is not None:
             return enc.get('url', '')
             
        # Check media:content (namespace)
        # Often looks like {http://search.yahoo.com/mrss/}content
        for child in item:
            if 'content' in child.tag and 'url' in child.attrib:
                # likely media:content
                return child.attrib['url']
            if 'thumbnail' in child.tag and 'url' in child.attrib:
                return child.attrib['url']
        return ""

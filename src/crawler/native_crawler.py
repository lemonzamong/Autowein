import urllib.request
import urllib.parse
import http.cookiejar
import re
import json
import time
import sys
import html as html_parser
from datetime import datetime

# Configuration
USERNAME = "june2450@naver.com"
PASSWORD = "june2450"
LOGIN_URL = "https://autowein.com/wp-login.php"
BASE_URL = "https://autowein.com"
API_URL = "https://autowein.com/wp-json/aw_post/id"
OUTPUT_FILE = "data/autowein_full_corpus.jsonl"
LIMIT_REAL = 100000 # Full history capture

def clean_html(text):
    if not text: return ""
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<style.*?>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    return html_parser.unescape(re.sub(r'\s+', ' ', text).strip())

def main():
    print(f"[Crawler] Starting API-based Full Crawl at {datetime.now()}")
    
    # 1. Setup Session
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), urllib.request.HTTPSHandler(debuglevel=0))
    opener.addheaders = [
        ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'),
        ('Referer', LOGIN_URL),
        ('Origin', BASE_URL)
    ]
    urllib.request.install_opener(opener)
    
    # 2. Login
    print("[Crawler] Attempting Login...")
    try:
        opener.open(LOGIN_URL) 
        login_data = urllib.parse.urlencode({
            'log': USERNAME, 'pwd': PASSWORD, 'rememberme': 'forever', 
            'wp-submit': '로그인', 'testcookie': '1', 'redirect_to': BASE_URL
        }).encode('utf-8')
        opener.open(LOGIN_URL, data=login_data)
        
        if any('wordpress_logged_in' in c.name for c in cj):
            print("[Crawler] Login SUCCESS!")
        else:
            print("[Crawler] Login FAILED. Content will be limited.")
            return # Critical failure
            
    except Exception as e:
        print(f"[Crawler] Login Error: {e}")
        return

    # 3. Discover IDs via Sitemap
    print("[Crawler] Parsing Sitemaps for IDs...")
    article_ids = set()
    try:
        sitemap_index_url = "https://autowein.com/sitemap_index.xml"
        resp = opener.open(sitemap_index_url)
        xml = resp.read().decode('utf-8')
        
        post_sitemaps = re.findall(r'<loc>(https://autowein\.com/.*?post-sitemap.*?\.xml)</loc>', xml)
        
        # Remove duplicates
        post_sitemaps = sorted(list(set(post_sitemaps)))
        
        print(f"[Crawler] Found {len(post_sitemaps)} sitemaps.")
        
        for i, sm_url in enumerate(post_sitemaps):
            if len(article_ids) >= LIMIT_REAL: break
            try:
                # print(f"  > Parsing sitemap {i+1}: {sm_url}...")
                sm_resp = opener.open(sm_url)
                sm_xml = sm_resp.read().decode('utf-8')
                urls = re.findall(r'<loc>(https://autowein\.com/.*?)</loc>', sm_xml)
                urls = [u for u in urls if u != sm_url and not u.endswith('.xml')]
                for u in urls:
                    # Extract ID from URL
                    # Pattern: /12345/ or /title-12345/
                    m = re.search(r'/(\d+)/?$', u)
                    if m:
                        article_ids.add(m.group(1))
            except Exception as e:
                print(f"  > Error parsing {sm_url}: {e}")
                
        print(f"[Crawler] Total IDs found: {len(article_ids)}")
        
    except Exception as e:
        print(f"[Crawler] Sitemap Discovery Failed: {e}")
    
    target_ids = list(article_ids)[:LIMIT_REAL]
    
    # 4. Fetch Details via API
    print(f"[Crawler] API Fetching for {len(target_ids)} items...")
    
    count_ok = 0
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for i, pid in enumerate(target_ids):
            try:
                if i % 10 == 0: 
                    print(f"  > Progress: {i}/{len(target_ids)} (Success: {count_ok})...")
                    f.flush()
                
                # API Call
                payload = urllib.parse.urlencode({
                    'post_id': pid,
                    'user_id': '0'
                }).encode('utf-8')
                
                req = urllib.request.Request(API_URL, data=payload, method='POST')
                req.add_header('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
                
                resp = opener.open(req)
                raw = resp.read().decode('utf-8')
                
                # Parse JSON
                try:
                    data = json.loads(raw)
                    if isinstance(data, list) and len(data) > 0:
                        p = data[0]
                        
                        # Process Fields
                        item = {
                            "id": str(p.get('id', pid)),
                            "url": f"https://autowein.com/{pid}/",
                            "title": clean_html(p.get('title', '')),
                            "text": clean_html(p.get('content', '')),
                            "comment": clean_html(p.get('comment', '')),  # Autowein's Comment
                            "tags": p.get('tags', []), # List of dicts or strings?
                            "related": [], # Placeholder, need to parse related_data if robust
                            "timestamp": datetime.now().isoformat() 
                        }
                        
                        # Tags cleanup (if list of dicts)
                        if isinstance(item['tags'], list):
                            clean_tags = []
                            for t in item['tags']:
                                if isinstance(t, dict) and 'name' in t:
                                    clean_tags.append("#" + t['name'].replace(" ", ""))
                                elif isinstance(t, str):
                                    clean_tags.append("#" + t.replace(" ", ""))
                            item['tags'] = clean_tags

                        # Related cleanup
                        if 'related_data' in p and p['related_data']:
                            item['related'] = p['related_data']

                        # Validation
                        if len(item['text']) > 10:
                            f.write(json.dumps(item, ensure_ascii=False) + '\n')
                            count_ok += 1
                        else:
                            # print(f"Skipping {pid}: Content empty")
                            pass
                            
                except Exception as json_err:
                    print(f"JSON Error for {pid}: {json_err}")

            except Exception as e:
                print(f"Error fetching {pid}: {e}")

    print(f"[Crawler] Done. Saved {count_ok} articles.")

if __name__ == "__main__":
    main()

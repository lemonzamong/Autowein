import urllib.request
import urllib.parse
import http.cookiejar
import re
import html as html_parser

USERNAME = "june2450@naver.com"
PASSWORD = "june2450"
LOGIN_URL = "https://autowein.com/wp-login.php"
BASE_URL = "https://autowein.com"
TARGET_URL = "https://autowein.com/7496/" # User's example (Volkswagen EV)

def clean_html(text):
    if not text: return ""
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<style.*?>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    return html_parser.unescape(re.sub(r'\s+', ' ', text).strip())

def main():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), urllib.request.HTTPSHandler(debuglevel=0))
    opener.addheaders = [
        ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'),
        ('Referer', LOGIN_URL),
        ('Origin', BASE_URL)
    ]
    urllib.request.install_opener(opener)

    print("--- 1. Login ---")
    opener.open(LOGIN_URL)
    login_data = urllib.parse.urlencode({
        'log': USERNAME, 'pwd': PASSWORD, 'rememberme': 'forever', 
        'wp-submit': '로그인', 'testcookie': '1', 'redirect_to': BASE_URL
    }).encode('utf-8')
    opener.open(LOGIN_URL, data=login_data)
    
    if any('wordpress_logged_in' in c.name for c in cj):
        print("Login Cookie: SUCCESS")
    else:
        print("Login Cookie: FAILED")

    print(f"\n--- 2. Fetching {TARGET_URL} ---")
    resp = opener.open(TARGET_URL)
    html = resp.read().decode('utf-8')
    
    if "Report 권한이 필요합니다" in html:
        print("ALERT: 'Report Permission Required' found!")
    else:
        print("Access seems OK.")

    # --- Extraction Logic for User Request ---
    
    # 1. Title
    t_match = re.search(r'<h1[^>]*>(.*?)</h1>', html)
    print(f"Title: {clean_html(t_match.group(1)) if t_match else 'Not Found'}")

    # 2. Tags (#Canada#China...)
    # Look for tags in standard WP locations or just hashtags in body
    print("\n[Tags]")
    tags = re.findall(r'#[\w\-&]+', html) 
    # Clean tags
    tags = list(set([t for t in tags if len(t) > 2 and not re.match(r'#[0-9a-f]{3,6}', t, re.I)]))
    print(tags[:10])

    # 3. Autowein's Comment
    print("\n[Autowein's Comment]")
    # First check JS variable 'v' which often holds the structured data
    comment_text = ""
    js_match = re.search(r'var v\s*=\s*({.*?});', html, re.DOTALL)
    if js_match:
        import json
        try:
            # Simple heuristic JSON parser or just regex
            c_match = re.search(r'["\']comment["\']\s*:\s*["\'](.*?)["\']', js_match.group(1), re.DOTALL)
            if c_match:
                comment_text = c_match.group(1)
                # Decode
                comment_text = bytes(comment_text, "utf-8").decode("unicode_escape")
        except: pass
    
    if not comment_text:
        # Check standard HTML for "Autowein's Comment" header and following p/div
        # Or <div id="aw-awm-comment">
        c_html = re.search(r'id=["\']aw-awm-comment["\'][^>]*>(.*?)</p>', html, re.DOTALL)
        if c_html: comment_text = c_html.group(1)
    
    print(clean_html(comment_text)[:300])

    # 4. Related Contents
    print("\n[Related Contents]")
    # Look for "Related Contents" or similar header
    if "Related Contents" in html:
        # Capture the list adjacent to it.
        # Often <div class="related-posts"> or similar
        rel_match = re.search(r'Related Contents(.*?)((<div class="row">)|(<footer>))', html, re.DOTALL)
        if rel_match:
            print(clean_html(rel_match.group(1))[:300])
    
    # 5. Full Body
    print("\n[Body Snippet]")
    body_match = re.search(r'class=["\']entry-content["\'][^>]*>(.*?)<div id="comments"', html, re.DOTALL)
    if body_match:
        print(clean_html(body_match.group(1))[:300])
    else:
        print("Body NOT found")

if __name__ == "__main__":
    main()

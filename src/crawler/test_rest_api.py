import urllib.request
import urllib.parse
import http.cookiejar
import json

USERNAME = "june2450@naver.com"
PASSWORD = "june2450"
LOGIN_URL = "https://autowein.com/wp-login.php"
# Found from source inspection
API_URL = "https://autowein.com/wp-json/aw_post/all"

def main():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [
        ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'),
        ('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8')
    ]
    urllib.request.install_opener(opener)

    print("Logging in...")
    opener.open(LOGIN_URL)
    login_data = urllib.parse.urlencode({
        'log': USERNAME, 'pwd': PASSWORD, 'wp-submit': '로그인', 'testcookie': '1', 'redirect_to': 'https://autowein.com/'
    }).encode('utf-8')
    opener.open(LOGIN_URL, data=login_data)
    
    # Check User ID extraction from page?
    # Or just try without it or with '0' first, or try to extract from cookies/page
    # Grep results might show it.
    
    # Construct Payload based on previous findings
    # type=10128 (News), by=?, user_id=?
    # Let's try guessing or grabbing from source if previous steps succeeded.
    
    # Mocking for now based on common patterns if grep fails
    payload = urllib.parse.urlencode({
        'by': 'category', # Common default
        'type': '10128',
        'paged': '1',
        'posts_per_page': '5',
        'user_id': '', # Try empty
        'keyword': ''
    }).encode('utf-8')
    
    print(f"Requesting {API_URL}...")
    try:
        req = urllib.request.Request(API_URL, data=payload, method='POST')
        resp = opener.open(req)
        data = resp.read().decode('utf-8')
        
        try:
            j = json.loads(data)
            print(f"Response Type: {type(j)}")
            if len(j) > 0 and 'posts' in j[0]:
                print(f"Posts found: {len(j[0]['posts'])}")
                p = j[0]['posts'][0]
                print(f"Sample Title: {p.get('title')}")
                print(f"Comment: {p.get('comment')}")
                print(f"Content: {p.get('content')}")
            else:
                print(f"JSON Structure unexpected: {data[:200]}")
        except:
            print(f"Not JSON: {data[:500]}")
            
    except Exception as e:
        print(f"Error: {e}")
        if hasattr(e, 'read'): print(e.read().decode())

if __name__ == "__main__":
    main()

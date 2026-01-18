import urllib.request
import urllib.parse
import json
import http.cookiejar

# Conf
USERNAME = "june2450@naver.com"
PASSWORD = "june2450"
LOGIN_URL = "https://autowein.com/wp-login.php"
BASE_URL = "https://autowein.com"
API_URL = "https://autowein.com/wp-json/aw_post/all"

# Found in debug_pagination.html
NONCE = "ce9e215154" 
USER_ID = "2394"

def main():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [
        ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'),
        ('Referer', LOGIN_URL)
    ]
    urllib.request.install_opener(opener)

    # 1. Login
    print("Logging in...")
    opener.open(LOGIN_URL)
    login_data = urllib.parse.urlencode({
        'log': USERNAME, 'pwd': PASSWORD, 'rememberme': 'forever', 
        'wp-submit': '로그인', 'testcookie': '1', 'redirect_to': BASE_URL
    }).encode('utf-8')
    opener.open(LOGIN_URL, data=login_data)
    
    if any('wordpress_logged_in' in c.name for c in cj):
        print("Login SUCCESS!")
    else:
        print("Login FAILED!")
        return

    # 2. Get Fresh Nonce
    print("Fetching Page 1 to extract Nonce...")
    nonce = ""
    try:
        resp = opener.open('https://autowein.com/post-list2/?type=news&awp=1&tv=1')
        html = resp.read().decode('utf-8')
        import re
        # Look for "ajax_nonce":"..."
        m = re.search(r'"ajax_nonce":"([a-f0-9]+)"', html)
        if m:
            nonce = m.group(1)
            print(f"Nonce Found: {nonce}")
        else:
            print("Nonce NOT found in HTML. Dumping head...")
            # print(html[:1000])
            return
    except Exception as e:
        print(f"Error fetching page: {e}")
        return

    # 3. Test Params with Fresh Headers
    headers = [
        ('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8'),
        ('X-Requested-With', 'XMLHttpRequest'),
        ('X-WP-Nonce', nonce), 
        ('Origin', 'https://autowein.com'),
        ('Referer', 'https://autowein.com/post-list2/?type=news&awp=1&tv=1')
    ]
    opener.addheaders = headers

    # Case: Proper payload
    payload = urllib.parse.urlencode({
        'by': '',
        'keyword': '',
        'type': '', 
        'paged': '1',
        'posts_per_page': '15',
        'user_id': USER_ID
    }).encode('utf-8')
    
    print("Requesting API with Login + Dynamic Nonce...")
    try:
        req = urllib.request.Request(API_URL, data=payload, method='POST')
        # Check if opener headers persist or need to be set on request
        # opener.addheaders are sent automatically.
        
        resp = opener.open(req)
        raw = resp.read().decode('utf-8')
        data = json.loads(raw)
        
        print(f"Response: Got {len(data)} items!")
        if len(data) > 0 and 'posts' in data[0]:
            print(f"Structure: {data[0].keys()}")
            print(f"First Post Title: {data[0]['posts'][0]['title']}")
        elif len(data) > 0:
            print(f"Unknown structure: {data[0]}")
            
    except Exception as e:
        print(f"Error: {e}")
        # print(f"Raw response maybe: {resp.read()}") # Cannot read closed

if __name__ == "__main__":
    main()

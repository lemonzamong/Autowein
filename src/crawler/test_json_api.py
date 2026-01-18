import urllib.request
import urllib.parse
import http.cookiejar
import json
import socket

USERNAME = "june2450@naver.com"
PASSWORD = "june2450"
LOGIN_URL = "https://autowein.com/wp-login.php"
# The discovered endpoint
API_URL = "https://autowein.com/wp-json/aw_post/id"
BASE_URL = "https://autowein.com"

def main():
    # Increase timeout
    socket.setdefaulttimeout(30)
    
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), urllib.request.HTTPSHandler(debuglevel=0))
    opener.addheaders = [
        ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'),
        ('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8'),
        ('Origin', BASE_URL),
        ('Referer', BASE_URL)
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
        print("Login SUCCESS")
    else:
        print("Login FAILED (Proceeding anyway)")

    print(f"\n--- 2. Requesting API {API_URL} for ID 7496 ---")
    payload = urllib.parse.urlencode({
        'post_id': '7496',
        'user_id': '0' # As seen in JS
    }).encode('utf-8')
    
    try:
        req = urllib.request.Request(API_URL, data=payload, method='POST')
        resp = opener.open(req)
        raw = resp.read().decode('utf-8')
        
        try:
            data = json.loads(raw)
            print(f"Response Type: {type(data)}")
            if isinstance(data, list) and len(data) > 0:
                item = data[0]
                print(f"Title: {item.get('post_title')}")
                print(f"Content Key Exists: {'post_content' in item}")
                print(f"Comment Key Exists: {'comment' in item}")
                
                # Check specifics
                print(f"\n[Related Data]\n{str(item.get('related_data'))[:500]}")
                
                # Check for Tags/Related? 
                # The JS `drawPost` uses `v` to render everything.
                # So `tags` and `related` should be in here too, possibly nested.
                print(f"\n[Keys]: {list(item.keys())}")
                
            else:
                print(f"Empty List or unexpected JSON: {raw[:200]}")
                
        except json.JSONDecodeError:
            print(f"Not JSON: {raw[:500]}")
            
    except Exception as e:
        print(f"API Request Failed: {e}")
        if hasattr(e, 'read'):
            print(f"Error Body: {e.read().decode()}")

if __name__ == "__main__":
    main()

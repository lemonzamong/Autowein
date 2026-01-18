import urllib.request
import urllib.parse
import http.cookiejar
import logging
import sys
import re
import json

# Setup logging to see headers
handler = urllib.request.HTTPSHandler(debuglevel=1)
opener = urllib.request.build_opener(handler)

USERNAME = "june2450@naver.com"
PASSWORD = "june2450" # Correted Password
LOGIN_URL = "https://autowein.com/wp-login.php"
BASE_URL = "https://autowein.com"
AJAX_URL = "https://autowein.com/wp-admin/admin-ajax.php"

def main():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), urllib.request.HTTPSHandler(debuglevel=0))
    opener.addheaders = [
        ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    ]
    urllib.request.install_opener(opener)

    print("--- 1. Initial Visit (Get Cookie) ---")
    opener.open(LOGIN_URL)
    print(f"Cookies: {[c.name for c in cj]}")

    print("\n--- 2. POST Login ---")
    login_data = urllib.parse.urlencode({
        'log': USERNAME,
        'pwd': PASSWORD,
        'rememberme': 'forever',
        'wp-submit': '로그인',
        'testcookie': '1',
        'redirect_to': BASE_URL
    }).encode('utf-8')

    try:
        resp = opener.open(LOGIN_URL, data=login_data)
        print(f"Response URL: {resp.geturl()}")
        print(f"Response Code: {resp.getcode()}")
        
        # Check Cookies
        cookies = {c.name: c.value for c in cj}
        print(f"Cookies: {list(cookies.keys())}")
        
        if any('wordpress_logged_in' in k for k in cookies):
            print(">>> LOGIN SUCCESS! <<<")
        else:
            print(">>> LOGIN FAILED (No logged_in cookie) <<<")
            # Print page text to see error message
            html = resp.read().decode('utf-8')
            if "login_error" in html:
                err = re.search(r'<div id="login_error">(.*?)</div>', html, re.DOTALL)
                if err:
                    print(f"Login Error Message: {re.sub('<[^>]+>', '', err.group(1)).strip()}")
            elif "SSO" in html or "kakao" in html:
                print("Page contains SSO/Kakao login elements. Possible interference?")

    except Exception as e:
        print(f"Login Exception: {e}")

    # 3. Try to get Nonce again from logged in (or not) state
    print("\n--- 3. Get Nonce ---")
    nonce = None
    try:
        html = opener.open("https://autowein.com/post-list2/?type=news").read().decode('utf-8')
        m = re.search(r'["\']ajax_nonce["\']\s*:\s*["\']([^"\']+)["\']', html)
        if m:
            nonce = m.group(1)
            print(f"Nonce: {nonce}")
    except:
        pass

    # 4. Try API with variations
    if nonce:
        print("\n--- 4. API Test with Nonce ---")
        # Variations
        payloads = [
            {'nonce': nonce},
            {'security': nonce},
            {'_ajax_nonce': nonce}
        ]
        
        for extra in payloads:
            print(f"Testing with extra param: {extra}")
            base_data = {
                'action': 'get_posts_list',
                'type': 'news',
                'paged': '1',
                'posts_per_page': '5'
            }
            base_data.update(extra)
            
            try:
                data_encoded = urllib.parse.urlencode(base_data).encode('utf-8')
                req = urllib.request.Request(AJAX_URL, data=data_encoded, headers={
                   'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                   'X-Requested-With': 'XMLHttpRequest',
                   'Referer': 'https://autowein.com/post-list2/?type=news'
                })
                resp = opener.open(req)
                res = resp.read().decode('utf-8')
                if res != '0':
                    print(f"SUCCESS! Length: {len(res)}. Start: {res[:50]}")
                    try:
                        j = json.loads(res)
                        if j and 'posts' in j[0]:
                            print("And it has posts!")
                            print("Keys in post:", j[0]['posts'][0].keys())
                            break
                    except:
                        pass
                else:
                    print("Returned 0")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    main()

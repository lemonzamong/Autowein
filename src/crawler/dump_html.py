import urllib.request
import urllib.parse
import http.cookiejar

USERNAME = "june2450@naver.com"
PASSWORD = "june2450"
LOGIN_URL = "https://autowein.com/wp-login.php"
BASE_URL = "https://autowein.com"
TARGET_URL = "https://autowein.com/7496/?nocache=1" # Add nocache param

def main():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj), urllib.request.HTTPSHandler(debuglevel=0))
    opener.addheaders = [
        ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'),
        ('Referer', LOGIN_URL)
    ]
    urllib.request.install_opener(opener)

    print("Logging in...")
    opener.open(LOGIN_URL)
    login_data = urllib.parse.urlencode({
        'log': USERNAME, 'pwd': PASSWORD, 'rememberme': 'forever', 
        'wp-submit': '로그인', 'testcookie': '1', 'redirect_to': BASE_URL
    }).encode('utf-8')
    opener.open(LOGIN_URL, data=login_data)

    print(f"Fetching {TARGET_URL}...")
    resp = opener.open(TARGET_URL)
    html = resp.read().decode('utf-8')
    
    with open("debug_7496.html", "w") as f:
        f.write(html)
    print("Saved to debug_7496.html")

if __name__ == "__main__":
    main()

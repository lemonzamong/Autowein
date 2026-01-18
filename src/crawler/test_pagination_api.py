import urllib.request
import urllib.parse
import json
import http.cookiejar

API_URL = "https://autowein.com/wp-json/aw_post/all"

def test_page(page_num):
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
    
    # Try mapping 'awp' logic to 'page' or 'paged'
    payload = urllib.parse.urlencode({
        'type': 'news',
        'page': page_num, 
        'posts_per_page': 15,
        'keyword': '',
        'by': 'all'
    }).encode('utf-8')
    
    try:
        req = urllib.request.Request(API_URL, data=payload, method='POST')
        resp = opener.open(req)
        data = json.loads(resp.read().decode('utf-8'))
        print(f"Page {page_num}: Got {len(data)} items. IDs: {[x.get('id') for x in data[:3]]}")
    except Exception as e:
        print(f"Page {page_num} Error: {e}")

if __name__ == "__main__":
    test_page(1)
    test_page(2)

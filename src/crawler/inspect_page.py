import requests
from bs4 import BeautifulSoup

def inspect_login():
    session = requests.Session()
    # Try common login paths
    urls = [
        "https://autowein.com/",
        "https://autowein.com/login", 
        "https://autowein.com/member/login"
    ]
    
    for url in urls:
        try:
            print(f"Checking {url}...")
            response = session.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                forms = soup.find_all('form')
                for i, form in enumerate(forms):
                    print(f"\n[Form {i} at {url}]")
                    print(f"Action: {form.get('action')}")
                    inputs = form.find_all('input')
                    for inp in inputs:
                        print(f" - Input: name='{inp.get('name')}', type='{inp.get('type')}'")
                    
                    # Check for keywords
                    text = form.text.lower()
                    if "id" in text or "login" in text or "email" in text:
                        print(" *** LIKELY LOGIN FORM ***")
        except Exception as e:
            print(f"Error fetching {url}: {e}")

if __name__ == "__main__":
    inspect_login()

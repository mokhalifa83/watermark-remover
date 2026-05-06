import requests
import time

def test_api(url):
    print(f"Testing URL: {url}")
    try:
        response = requests.post(
            'http://127.0.0.1:5000/api/remove-watermark',
            json={'url': url},
            timeout=30
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    # Sample URLs - I'll use real ones if I find them in history, 
    # but for now I'll just see if I can run the server and test it.
    # Actually, I can't easily run the server and test it in one go if I don't have real URLs.
    
    # Let's try to find a real URL from the project files.
    pass

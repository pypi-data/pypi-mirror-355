import json
import os
import requests

def run_test(test_file):
    with open(test_file, 'r') as f:
        test = json.load(f)

    url = test['url']
    method = test['method'].upper()
    headers = test.get('headers', {})
    data = test.get('body')

    try:
        response = requests.request(method, url, headers=headers, json=data)

        # Try parsing JSON
        try:
            resp_json = response.json() if response.content else {}
        except json.JSONDecodeError:
            resp_json = {}

        print(f"\n📤 {method} {url}")
        print(f"📥 Status: {response.status_code} {response.reason}")
        
        # Print response content
        print("📦 Response:")
        if resp_json:
            print(json.dumps(resp_json, indent=2))
        else:
            print(response.text or "(No content)")

    except Exception as e:
        print(f"❌ Error running {test_file}: {e}")


def create_test_interactively():
    os.makedirs("tests", exist_ok=True)

    url = input("📍 Enter endpoint URL: ").strip()
    method = input("📤 Method? (GET/POST/PUT/DELETE): ").strip().upper()
    body_raw = input("🧾 Body (JSON, optional): ").strip()

    try:
        body = json.loads(body_raw) if body_raw else None
    except json.JSONDecodeError:
        print("❌ Invalid JSON body.")
        return

    test_data = {
        "url": url,
        "method": method,
        "body": body
    }

    # Filename based on URL
    last_segment = url.strip('/').split('/')[-1] or "root"
    filename = f"tests/test_{method.lower()}_{last_segment}.json"

    with open(filename, 'w') as f:
        json.dump(test_data, f, indent=2)

    print(f"✅ Test saved to {filename}")
    print(f"▶️ To run this test: `apitester-lite run {filename}`")

import requests
import json

def test_case_1():
    url = "http://127.0.0.1:8000/api/kpi/calculate-all-routes"
    try:
        response = requests.post(url)
        print(f"Status Code: {response.status_code}")
        data = response.json()
        print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_case_1()

import requests
import os
import time

BASE = os.getenv("API_URL", "http://localhost:8000")


def test_search_endpoint():
    url = f"{BASE}/search"
    r = requests.post(url, json={"query": "test query"}, timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert "results" in data


if __name__ == "__main__":
    test_search_endpoint()
    print("search smoke test passed")

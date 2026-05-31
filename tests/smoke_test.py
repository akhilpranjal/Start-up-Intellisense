import requests

API = "http://localhost:8000"


def main():
    print("Running smoke tests against", API)
    try:
        r = requests.get(f"{API}/health", timeout=5)
        print("/health ->", r.status_code, r.json())
    except Exception as e:
        print("/health failed:", e)
        return

    payload = {"source": "test", "raw_text": "Startup: DemoX\nWe build useful demo software.", "metadata": {"test": True}}
    try:
        r = requests.post(f"{API}/ingest", json=payload, timeout=5)
        print("/ingest ->", r.status_code, r.json())
    except Exception as e:
        print("/ingest failed:", e)


if __name__ == "__main__":
    main()

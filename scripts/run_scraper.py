"""Small CLI to run YC Playwright scraper for demo purposes."""
import sys
from pathlib import Path

# Allow `python scripts/run_scraper.py ...` from repo root
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scrapers.yc_playwright import scrape_yc_companies
from scrapers.base import persist_raw
from app.db import SessionLocal
import os
import redis
from rq import Queue

from workers.tasks import process_raw


def main():
    if len(sys.argv) < 2:
        print("usage: python scripts/run_scraper.py yc [max_pages]")
        raise SystemExit(1)

    typ = sys.argv[1]
    if typ == "yc":
        max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        out = scrape_yc_companies(max_pages=max_pages)
        if not out:
            print("No results from scraper")
            return

        db = SessionLocal()
        try:
            for item in out:
                # persist raw scrape record
                rec = persist_raw(db, source=item.get("source", "yc"), raw_text=item.get("description", ""), metadata=item)
                print(f"Persisted raw id={rec.id} name={item.get('name')}")

                # try enqueueing processing, fall back to inline processing
                try:
                    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
                    redis_conn = redis.from_url(redis_url, protocol=2)
                    q = Queue("default", connection=redis_conn)
                    q.enqueue("workers.tasks.process_raw", rec.id)
                    print(f"Enqueued processing for raw id={rec.id}")
                except Exception:
                    outp = process_raw(rec.id)
                    print(f"Processed inline for raw id={rec.id}: {outp}")
        finally:
            db.close()
    else:
        print("unknown type; use: yc")


if __name__ == "__main__":
    main()

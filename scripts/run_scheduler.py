"""Run scheduled YC scraper jobs and enqueue processing tasks."""
import sys
from pathlib import Path

# Allow `python scripts/run_scheduler.py` from repo root
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apscheduler.schedulers.blocking import BlockingScheduler
from app.db import SessionLocal
from scrapers.yc_playwright import scrape_yc_companies
from scrapers.base import persist_raw
import traceback
import os
import redis
from rq import Queue

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


def job_yc():
    try:
        items = scrape_yc_companies(max_pages=1)
        db = SessionLocal()
        redis_conn = redis.from_url(REDIS_URL, protocol=2)
        q = Queue("default", connection=redis_conn)
        for it in items:
            rec = persist_raw(db, source="yc", raw_text=it.get("description") or it.get("name") or "", metadata=it)
            q.enqueue("workers.tasks.process_raw", rec.id)
        db.close()
        print("yc job enqueued")
    except Exception:
        traceback.print_exc()


def main():
    sched = BlockingScheduler()
    # Run at startup and then every 6 hours
    sched.add_job(job_yc, "interval", hours=6, next_run_time=None)
    print("YC scheduler started: running every 6 hours")
    sched.start()


if __name__ == "__main__":
    main()

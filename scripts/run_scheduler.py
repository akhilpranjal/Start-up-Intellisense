"""Run scheduled YC scraper jobs and enqueue processing tasks."""
import sys
from pathlib import Path

# Allow `python scripts/run_scheduler.py` from repo root
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from apscheduler.schedulers.blocking import BlockingScheduler
import traceback
import os
import redis
from rq import Queue

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


def job_yc():
    try:
        redis_conn = redis.from_url(REDIS_URL, protocol=2)
        q = Queue("default", connection=redis_conn)
        q.enqueue("workers.tasks.scrape_and_process_yc", 1)
        print("yc scrape job enqueued")
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

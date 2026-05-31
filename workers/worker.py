import os
import redis
from rq import Queue, Worker

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


def run_worker():
    redis_conn = redis.from_url(REDIS_URL, protocol=2)
    q = Queue("default", connection=redis_conn)
    worker = Worker([q], connection=redis_conn)
    worker.work()


if __name__ == "__main__":
    run_worker()

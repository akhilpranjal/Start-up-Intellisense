import os
import redis
from rq import Queue, Worker, Connection

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


def run_worker():
    redis_conn = redis.from_url(REDIS_URL)
    with Connection(redis_conn):
        q = Queue("default")
        worker = Worker([q])
        worker.work()


if __name__ == "__main__":
    run_worker()

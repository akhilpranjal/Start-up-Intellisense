.PHONY: up api worker reindex test

up:
	docker compose up -d redis qdrant

api:
	uvicorn app.api:app --reload --port 8000

worker:
	rq worker default

reindex:
	python scripts/reindex_qdrant.py

test:
	python tests/smoke_test.py && python tests/smoke_test_search.py

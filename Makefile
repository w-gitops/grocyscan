.PHONY: test test-db-up test-db-down

TEST_DATABASE_URL ?= postgresql+asyncpg://grocyscan:grocyscan@localhost:5432/grocyscan_test

test-db-up:
	docker compose -f docker/docker-compose.test.yml up -d

test-db-down:
	docker compose -f docker/docker-compose.test.yml down -v

test:
	DATABASE_URL=$(TEST_DATABASE_URL) python -m pytest tests/ -v --tb=short

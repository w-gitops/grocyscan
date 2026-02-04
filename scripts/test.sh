#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

DB_URL_DEFAULT="postgresql+asyncpg://grocyscan:grocyscan@localhost:5432/grocyscan_test"
DB_URL="${DATABASE_URL:-$DB_URL_DEFAULT}"

echo "Using DATABASE_URL=${DB_URL}"
cd "${ROOT_DIR}"

if command -v docker >/dev/null 2>&1; then
  if ! docker compose -f docker/docker-compose.test.yml ps -q postgres >/dev/null 2>&1; then
    echo "Starting test Postgres..."
    docker compose -f docker/docker-compose.test.yml up -d
  fi
else
  echo "Warning: docker not available; assuming Postgres is running."
fi

DATABASE_URL="${DB_URL}" python -m pytest tests/ -v --tb=short

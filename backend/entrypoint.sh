#!/bin/bash
set -e

echo "=== Waiting for database ==="
python wait_for_db.py

echo "=== Running migrations ==="
alembic upgrade head

echo "=== Checking whether ingestion is needed ==="
NEEDS_INGEST=$(python -c "
from app.database import SessionLocal
from app.models import Paper
db = SessionLocal()
count = db.query(Paper).count()
db.close()
print('yes' if count == 0 else 'no')
")

if [ "$NEEDS_INGEST" = "yes" ]; then
    echo "=== No papers found - running ingestion (this can take a few minutes) ==="
    python -m ingestion.ingest_openalex
else
    echo "=== Papers already present - skipping ingestion ==="
    echo "(re-run manually with: docker compose exec backend python -m ingestion.ingest_openalex)"
fi

echo "=== Starting API server ==="
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
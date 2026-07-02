#!/bin/sh
set -e

# DBが立ち上がるまで待つ（compose の healthcheck と二重の保険）
echo "[entrypoint] waiting for db..."
python - <<'PY'
import os, time
import psycopg
url = os.environ["DATABASE_URL"].replace("+psycopg", "")
for i in range(30):
    try:
        psycopg.connect(url).close()
        print("[entrypoint] db is ready")
        break
    except Exception as e:
        print(f"[entrypoint] db not ready ({i}): {e}")
        time.sleep(2)
else:
    raise SystemExit("db did not become ready")
PY

echo "[entrypoint] alembic upgrade head"
alembic upgrade head

echo "[entrypoint] seed admin"
python -m app.seed

echo "[entrypoint] start uvicorn"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 ${UVICORN_RELOAD:+--reload}

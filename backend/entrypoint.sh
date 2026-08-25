#!/bin/sh
# Aplica las migraciones y arranca uvicorn. Alembic es idempotente: si el
# esquema ya esta al dia, `upgrade head` no hace nada y el arranque sigue.
set -eu

echo "entrypoint: alembic upgrade head"
alembic upgrade head

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"

#!/bin/sh
# Aplica las migraciones y arranca uvicorn. Alembic es idempotente: si el esquema
# ya esta al dia, `upgrade head` no hace nada.
#
# Con SEED_DEMO=1 el contenedor tambien se autoabastece: siembra la temporada de
# demo y crea el administrador. Existe porque la RDS es privada y no se puede
# sembrar desde fuera de la VPC. Ambos scripts son idempotentes, asi que un
# reinicio del task no duplica nada.
set -eu

echo "entrypoint: alembic upgrade head"
alembic upgrade head

if [ "${SEED_DEMO:-0}" = "1" ]; then
  echo "entrypoint: sembrando datos de demo"
  python scripts/seed_demo.py
  if [ -n "${ADMIN_EMAIL:-}" ]; then
    python scripts/bootstrap_admin.py
  fi
fi

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"

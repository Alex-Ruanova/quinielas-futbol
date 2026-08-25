# Quinielas de Fútbol

Plataforma de quinielas donde los usuarios pronostican resultados para acumular **puntos**
y apuestan **créditos virtuales** en dos mercados: el resultado del partido (1X2) y la
**franja de 15 minutos en la que caerá un gol**. El momio se deriva de la fuerza relativa
de los equipos: apostarle al grande paga poco, al chico paga mucho.

Los créditos son virtuales y no canjeables. No hay dinero real, depósitos, retiros ni
pasarela de pago — ver [`docs/quinielas-futbol/prd.md`](docs/quinielas-futbol/prd.md).

## Arquitectura

Tres capas y un núcleo puro:

```
app/api/       routers FastAPI, DTOs, códigos de estado
      │
app/services/  lógica transaccional: apostar, liquidar, cancelar, registrar
      │                    │
app/engine/    app/models/  (SQLAlchemy)
  (PURO)
```

`app/engine/` no importa `sqlalchemy`, `fastapi` ni nada con I/O, y nunca llama
`datetime.now()` — el instante entra por parámetro. Eso se verifica con `grep` y, sobre
todo, corriendo sus tests **con PostgreSQL apagado**.

| Regla | Vive en |
|---|---|
| R1 momios, R2 franjas, R8 puntuación | `app/engine/` — funciones puras |
| R3 cierre de apuestas | `engine/rules.py::is_open_for_betting(kickoff_at, now)` |
| R4 momio congelado | `bets.odds_snapshot` + `services/betting.py` |
| R5 ledger append-only | `services/wallet.py` — única puerta de escritura |
| R6 liquidación idempotente | `services/settlement.py` + bloqueo pesimista |
| R9 cancelación | `services/settlement.py::cancel_match` |

## Arrancar en local

Requisitos: Docker, Python 3.13 con [uv](https://docs.astral.sh/uv/), Node 22.

```bash
# 1. Base de datos
docker compose up -d db

# 2. Backend
cd backend
uv sync
cp .env.example .env          # ajusta JWT_SECRET si quieres
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

API en `http://localhost:8000`, documentación interactiva en `/docs`.

```bash
# 3. Datos de demo
uv run python scripts/seed_demo.py

# 4. Un administrador
uv run python scripts/create_admin.py tu@correo.mx
```

## Verificar

```bash
cd backend

uv run pytest tests/ -v            # suite completa
uv run mypy --strict app           # tipado
uv run ruff check app tests        # lint

# El gate que importa: el motor no toca la base.
docker compose stop db
uv run pytest tests/engine/ -v     # tiene que pasar igual, en <2s
docker compose start db
```

Los invariantes arquitectónicos son grepeables:

```bash
grep -rnE "sqlalchemy|fastapi|datetime\.now|from app\." backend/app/engine/   # A1, A2
grep -rn  "HTTPException" backend/app/services/ backend/app/engine/           # A4
grep -rnE "\* *odds|HOME_ADVANTAGE|DRAW_BASE" backend/app/services/           # A5
```

Los tres deben salir vacíos.

## El requisito central

Para todo par de fuerzas `(1..100, 1..100)` con `strength_home > strength_away`, se cumple
`odds_home < odds_away`. Verificado sobre los 10 000 pares, sin excepciones:

```
rival_strength     local      empate     visita
  10               1.10       18.86      11.12
  50               1.74        5.13       3.53
  100              2.62        3.41       2.65
```

Existe margen de la casa en todo el dominio (`1/odds_home + 1/odds_draw + 1/odds_away > 1`),
con mínimo `1.004845` en el par extremo `(100, 1)`, donde el clamp `MIN_ODDS = 1.01` lo
erosiona pero no lo elimina.

## Documentación

| Documento | Qué contiene |
|---|---|
| [`docs/quinielas-futbol/prd.md`](docs/quinielas-futbol/prd.md) | PRD: reglas R1–R9, arquitectura A1–A5, plan por fases |
| [`docs/quinielas-futbol/design-prd.md`](docs/quinielas-futbol/design-prd.md) | PRD de diseño |
| [`docs/quinielas-futbol/design/`](docs/quinielas-futbol/design/) | Canvas, `tokens.md` y verificación del DoD de diseño |
| [`docs/specs/`](docs/specs/) | Especificación técnica de cada fase |

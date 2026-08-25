# Spec — Phase 2: Fundación (modelo de datos y andamiaje)

## Goal
Esqueleto del backend FastAPI y esquema completo de PostgreSQL con migración Alembic
reversible. Es la base de la que dependen las Phases 4, 5 y 6.

## Entorno ya provisto (no crearlo)
- PostgreSQL 16.14 corriendo vía `docker-compose.yml` en la raíz del repo (ya commiteado).
- `DATABASE_URL=postgresql+psycopg://quinielas:quinielas@localhost:5432/quinielas`
- Bases adicionales ya creadas para fases paralelas: `quinielas_p4`, `quinielas_p5`.

## Data Structures (SQLAlchemy 2.0 declarativo tipado, `Mapped[...]`/`mapped_column`)
- `Team(id UUID pk, name, strength int CHECK 1..100, crest_url NULL)`
- `Season(id, name, starts_on date, ends_on date, scoring_config JSONB NULL, status)`
- `Round(id, season_id FK, number int, name, opens_at TIMESTAMPTZ, closes_at TIMESTAMPTZ)`
- `Match(id, round_id FK, home_team_id FK, away_team_id FK, kickoff_at TIMESTAMPTZ,
   status ENUM[SCHEDULED,FINISHED,CANCELLED], home_score NULL, away_score NULL, settled_at NULL)`
- `Goal(id, match_id FK, team_id FK, minute int, is_stoppage bool)`
- `User(id, email UNIQUE, password_hash, display_name, phone NULL, contact_email NULL,
   is_admin bool default false, created_at)`
- `CreditTransaction(id, user_id FK, kind ENUM[SEED,STAKE,PAYOUT,REFUND],
   amount NUMERIC(12,2), bet_id NULL, created_at)` — append-only
- `Prediction(id, user_id FK, match_id FK, predicted_home_score, predicted_away_score,
   points_awarded NULL)` con `UNIQUE(user_id, match_id)`
- `Bet(id, user_id FK, match_id FK, market ENUM[OUTCOME,GOAL_BAND], selection JSONB,
   stake NUMERIC(12,2), odds_snapshot NUMERIC(6,2),
   status ENUM[PENDING,WON,LOST,VOID], settled_at NULL, created_at)`

**Invariante dura:** toda columna de dinero es `NUMERIC(12,2)` mapeada a `Decimal`.
Nunca `Float` ni `DOUBLE`.

## Implementation Steps
1. `backend/pyproject.toml` con las deps del PRD Task 2.2. Paquete `app`.
2. `app/core/config.py` — `Settings(BaseSettings)` con `database_url`, `jwt_secret`,
   `jwt_algorithm`, `access_token_ttl_minutes`. Lee de env con prefijo, `.env` opcional.
3. `app/db/base.py` — `class Base(DeclarativeBase)`. `app/db/session.py` — engine,
   `SessionLocal`, y dependencia `get_session()` inyectable que hace rollback en excepción.
4. `app/models/` — un módulo por agregado + `__init__.py` que reexporta todo para que
   Alembic autogenere con el metadata completo. Enums como `sqlalchemy.Enum` nativos de PG.
5. `alembic/` inicializado, `env.py` leyendo `Settings.database_url` y `Base.metadata`.
   Una única migración inicial con todos los índices:
   `matches(round_id, kickoff_at)`, `bets(match_id, status)`, `credit_transactions(user_id)`.
6. `tests/conftest.py` — fixture `session` por test (conexión + transacción externa con
   rollback, sin recrear el esquema por test) y fixture `client` httpx/ASGI. Sin mocking.

## Edge Cases
- El CHECK de `strength` tiene que vivir en la base, no solo en Python.
- `downgrade` debe borrar también los tipos ENUM de PostgreSQL, o el ciclo
  `downgrade base && upgrade head` falla en el segundo `upgrade`. Es el error clásico aquí.
- Todas las columnas de tiempo son `TIMESTAMPTZ`, jamás `TIMESTAMP` naive.

## Testing Plan (ligero — decisión explícita de Alex por tiempo de entrevista)
`tests/models/test_schema.py`, solo lo que prueba que el esquema es real:
1. `Team` con `strength=0` y con `strength=101` → `IntegrityError` de la base.
2. `Prediction` duplicado en `(user_id, match_id)` → `IntegrityError`.
3. Un `Match` con equipos y goles se persiste y se relee con los tipos correctos
   (`Decimal` donde toca).
No se piden tests de concurrencia ni de atomicidad en esta fase.

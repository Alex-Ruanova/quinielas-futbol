# Spec — Phase 5: API de administración — catálogo

## Goal
Todo lo que el admin necesita para armar una temporada: equipos, temporadas, jornadas y
partidos. La captura de resultados **no** va aquí — vive en la Phase 6, junto a la
liquidación, porque son la misma operación transaccional.

## Entorno
`DATABASE_URL=postgresql+psycopg://quinielas:quinielas@localhost:5432/quinielas_p5`
(base propia para no chocar con la Phase 4, que corre en paralelo).
El esquema ya existe vía Alembic (Phase 2). El motor puro ya existe en `app/engine/`
(Phase 3). `core/security.py` con `require_admin` y `app/main.py` los aporta la Phase 4,
que corre **en paralelo** — ver la nota de scope abajo.

## Nota de scope (importante)
`app/main.py`, `core/security.py` y `api/exception_handlers.py` pertenecen a la Phase 4 y
**no** están en tu `file_scope`. Tampoco los necesitas crear: la Phase 4 ya registra
`app.api.admin.catalog` en su lista de includes tolerantes, así que tu router queda
cableado al fusionarse. Importa `require_admin` desde `app.core.security` con normalidad:
si el módulo aún no existe en tu worktree, **no lo crees** — reporta el import faltante
en `outOfScopeIssues` y sigue. El merge lo resuelve.

## Implementation Steps
1. `schemas/catalog.py` — DTOs de create/update/read para `Team`, `Season`, `Round`,
   `Match`, más `OddsPreview`.
2. `services/catalog.py` — CRUD transaccional, con las validaciones de negocio:
   - Los dos equipos de un partido son **distintos** → `InvalidSelection`.
   - `kickoff_at` cae dentro de `[round.opens_at, round.closes_at]` → `InvalidSelection`.
   - `strength` en `1..100` (Pydantic lo valida con `Field(ge=1, le=100)`; la base tiene
     además el CHECK de la Phase 2).
   - `odds_preview(strength, opponent_strength) -> MatchOdds` delegando a
     `app.engine.odds.compute_odds`. **Cero aritmética de momios aquí** (A5).
3. `api/admin/__init__.py` y `api/admin/catalog.py` — router con prefijo
   `/api/v1/admin`, **todo** bajo `dependencies=[Depends(require_admin)]`:
   - `POST|GET|PATCH|DELETE /admin/teams`, `/admin/seasons`, `/admin/rounds`, `/admin/matches`
   - `PATCH /admin/seasons/{id}/scoring` — edita `scoring_config` (puntos por acierto y
     momio por franja)
   - `GET /admin/teams/{id}/odds-preview?opponent_strength=N` — alimenta el slider del
     panel de admin
4. `scripts/seed_demo.py` — una temporada, dos jornadas, ocho equipos con `strength`
   deliberadamente dispares (p. ej. 92 y 24) y partidos en el **futuro**, para que el
   sistema se pueda navegar de inmediato. Idempotente: si ya sembró, no duplica.

## Edge Cases
- Los `422` de las validaciones de negocio salen del handler único de la Phase 4
  traduciendo `InvalidSelection`. No lances `HTTPException` desde `services/` (A4).
- `scoring_config` es un JSONB parcial: se hace merge clave por clave contra los defaults
  del motor (`ScoringRules.from_config`), nunca se sustituye el bloque completo.

## Testing Plan (ligero — decisión explícita de Alex)
`tests/api/test_admin_catalog.py`:
1. Partido con el mismo equipo de local y visitante → 422.
2. Partido con `kickoff_at` fuera de la ventana de su jornada → 422.
3. `strength` 0 o 101 → 422.
4. Usuario no-admin → 403 en los endpoints de `/admin/`.
5. `odds-preview` con `strength=92` contra `opponent_strength=24` → `odds_home < odds_away`.
6. `python scripts/seed_demo.py` corre y deja la temporada navegable (salida mostrada).

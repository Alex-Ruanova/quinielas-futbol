# Spec — Phase 6: Juego — pronósticos, apuestas, resultados y liquidación

## Goal
El ciclo completo del juego: el usuario pronostica y apuesta, el admin captura el
resultado con el minuto de cada gol, y el sistema liquida pagos y puntos. Es la fase más
pesada del backend y donde se concentran los tests que importan.

## Regla dominante: estos servicios NO calculan, orquestan
Toda la aritmética vive en `app/engine/` (A5). Un servicio que multiplique un stake por un
momio está mal escrito. Los servicios construyen DTOs del motor a partir de las filas ORM,
llaman al motor, y persisten el resultado. El motor **nunca** recibe un objeto SQLAlchemy.

## Entorno
`DATABASE_URL=postgresql+psycopg://quinielas:quinielas@localhost:5432/quinielas`
Ya existen: los 9 modelos, el motor puro, `services/wallet.py`, `services/catalog.py`,
`core/security.py`, `api/exception_handlers.py` y `app/main.py` con los includes tolerantes
que ya registran `app.api.matches`, `app.api.bets`, `app.api.leaderboard` y
`app.api.admin.results`. **No toques `main.py`: tu router queda cableado solo.**

## Implementation Steps

### `services/betting.py::place_bet` — una sola transacción
Orden estricto, todo dentro de una transacción:
1. Carga el `Match` (404 vía `NotFound` si no existe).
2. `engine.rules.is_open_for_betting(match.kickoff_at, now)` con el `now` **del servidor**
   pasado por parámetro (A2). Si es `False` → `BettingClosed` (409).
3. `engine.rules.validate_stake(stake)` → `StakeOutOfRange` (422).
4. Valida la **forma** de la selection con `engine/selection.py`.
5. Valida la **pertenencia**: si es `GOAL_BAND` con `team_id`, ese equipo tiene que ser el
   local o el visitante de ese partido → `InvalidSelection` (422). Esto es lo que el motor
   no puede hacer porque requiere la base.
6. Calcula el momio: `OUTCOME` → `engine.odds.compute_odds` sobre las `strength` actuales,
   tomando la rama de la selección; `GOAL_BAND` → el momio de esa franja desde
   `season.scoring_config`, con fallback a `DEFAULT_GOAL_BAND_ODDS`.
7. **Congela** ese momio en `bet.odds_snapshot` (R4).
8. Debita con `services/wallet.py::debit` (la única puerta al ledger) → `InsufficientCredits` (402).
9. Crea el `Bet` en `PENDING`.

La atomicidad va en ambas direcciones: si el `INSERT` del `Bet` falla tras el débito, el
asiento `STAKE` tampoco puede persistir. Una sola transacción lo garantiza — no uses
commits intermedios.

### `services/results.py::record_result`
`{home_score, away_score, goals: [{team_id, minute, is_stoppage}]}`:
- El número de goles del arreglo tiene que cuadrar con `home_score + away_score`, y el
  reparto por equipo también → `InvalidSelection` (422), sin persistir nada.
- Cada `team_id` juega ese partido → 422.
- Persiste los `Goal`, marca el `Match` como `FINISHED`, y dispara `settle_match` en la
  **misma** transacción.

### `services/settlement.py::settle_match` — idempotente (R6)
- Carga las apuestas del partido con `SELECT ... FOR UPDATE` filtrando `status = PENDING`.
  Las ya liquidadas no vuelven a entrar: ahí está la idempotencia. Invocarla tres veces
  produce el mismo balance y el mismo número de transacciones que invocarla una vez.
- Construye `BetInput` y `MatchResult` (DTOs del motor) y delega en `engine.resolution.resolve_bet`.
- Acredita los pagos vía `wallet.credit` con kind `PAYOUT`.
- Puntúa los pronósticos con `engine.scoring.score_prediction`, usando
  `ScoringRules.from_config(season.scoring_config)`. Escribe `prediction.points_awarded`.
- Marca `bet.settled_at` y `match.settled_at`.

`cancel_match` (R9): todas las apuestas a `VOID`, reembolso íntegro del stake con kind
`REFUND`, y **cero** puntos otorgados.

### Endpoints
- `GET /api/v1/matches/upcoming` — partidos futuros con equipos, `kickoff_at`, momios de
  resultado calculados **en vivo**, momios de franja, y el pronóstico y apuestas propias.
- `PUT /api/v1/matches/{id}/prediction` — crea o reemplaza; idempotente sobre `(user, match)`.
- `POST /api/v1/matches/{id}/bets`
- `PUT /api/v1/admin/matches/{id}/result`, `POST /api/v1/admin/matches/{id}/settle`,
  y la cancelación. Todo bajo `require_admin`.
- `GET /api/v1/bets` (propias, filtrables por estado)
- `GET /api/v1/seasons/{id}/leaderboard` — orden por puntos, desempate por marcadores
  exactos, luego por balance.
- `GET /api/v1/rounds/{id}/results`

## Edge Cases
- `R7`: puntos y créditos son ejes independientes. Un usuario que solo pronosticó y no
  apostó recibe puntos y aparece en el leaderboard con el balance intacto. Son dos rutas
  de código sin acoplamiento — no las unifiques por parecer más limpias.
- El leaderboard sobre `predictions` puede ser una query pesada; agrega por `SUM(points_awarded)`
  en la base, no en Python.
- `scoring_config` malformado (lo edita un admin) no puede reventar en 500: si
  `ScoringRules.from_config` recibe basura, tiene que salir un error de dominio.

## Testing Plan (ligero — decisión explícita de Alex)
Los que prueban el producto, no la cobertura:
1. Apostar 100 con balance 1000 → balance 900 y `Bet` `PENDING` con `odds_snapshot` no nulo.
2. Apostar sobre un partido cuyo `kickoff_at` ya pasó → 409, balance sin cambios.
3. Stake 5 o 501 → 422. Balance insuficiente → 402 sin crear `Bet` ni transacción.
4. **Crítico R4:** se coloca una apuesta, el admin cambia `team.strength`, y el
   `odds_snapshot` de la apuesta existente permanece idéntico.
5. **Crítico R6:** invocar `settle_match` tres veces produce el mismo balance y el mismo
   número de transacciones que invocarla una vez.
6. `GOAL_BAND` con un `team_id` que no juega ese partido → 422 y no debita nada.
7. **E2E por HTTP:** partido 2-1, goles al 12 y 70 (local) y 55 (visitante). Un usuario
   apuesta `HOME`, otro la franja `61-75`. Ambos ganan y su balance sube exactamente
   `stake * odds_snapshot`.
8. **R9:** cancelar un partido con dos apuestas las deja en `VOID`, reembolsa el stake
   exacto y no otorga puntos.
9. **R7:** un usuario que solo pronosticó recibe puntos con el balance intacto.

Quedan **fuera** por tiempo: los tests de concurrencia (dos liquidaciones simultáneas,
dos débitos simultáneos) y el test de atomicidad inversa. El `SELECT ... FOR UPDATE` se
implementa igual.

## Gates
- `grep -rnE "\* *odds|HOME_ADVANTAGE|DRAW_BASE" backend/app/services/` sin coincidencias (A5).
- `grep -rn "HTTPException" backend/app/services/ backend/app/engine/` sin coincidencias (A4).
- `mypy --strict app`, `ruff check`, y `pytest tests/engine/` con PostgreSQL detenido.

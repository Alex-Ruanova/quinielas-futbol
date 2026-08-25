# Spec — Phase 3: Motor puro (momios, franjas, puntuación, resolución)

## Goal
El núcleo de valor del producto: funciones puras, sin DB ni I/O, con tests instantáneos.
Es la única fase que se construye contra un repo vacío.

## Regla arquitectónica dura (A1/A2 — se verifica con grep en el DoD)
Ningún módulo de `app/engine/` importa `sqlalchemy`, `fastapi`, ni `app.*`, ni llama
`datetime.now()`/`utcnow()`. El instante entra siempre por parámetro.
Solo stdlib + Pydantic. Todos los DTOs son `model_config = ConfigDict(frozen=True)`.

## Aritmética exacta
`Decimal` para dinero y momios, `float` solo dentro del cálculo de probabilidades de R1.
Redondeo de momios y pagos: `Decimal.quantize(Decimal("0.01"), ROUND_HALF_UP)`.

## Módulos
- `config.py` — **única** fuente de: `HOME_ADVANTAGE=0.10`, `DRAW_BASE=0.28`,
  `MARGIN=0.05`, `MIN_ODDS=Decimal("1.01")`, `SEED_CREDITS=Decimal("1000.00")`,
  `MIN_STAKE=Decimal("10.00")`, `MAX_STAKE=Decimal("500.00")`,
  `DEFAULT_GOAL_BAND_ODDS=Decimal("4.50")`, y defaults de scoring
  (`outcome=3`, `exact_score=5`, `goal_band=2`). Sin imports del resto de la app.
- `errors.py` — `DomainError` base, y `BettingClosed`, `InsufficientCredits`,
  `StakeOutOfRange`, `AlreadySettled`, `InvalidSelection`, `NotFound`.
  Ninguno hereda de `HTTPException`.
- `odds.py` — `compute_odds(strength_home: int, strength_away: int, config: OddsConfig)
  -> MatchOdds` exactamente según R1. `OddsConfig`/`MatchOdds` frozen.
- `bands.py` — `GoalBand` StrEnum con `0-15,16-30,31-45,46-60,61-75,76-90+`;
  `band_for_minute(minute, is_stoppage) -> GoalBand`.
- `scoring.py` — `Score` frozen; `ScoringRules` frozen con
  `from_config(raw: dict | None) -> ScoringRules` que hace merge **clave por clave**
  sobre los defaults (no bloque completo); `score_prediction(predicted, actual, rules) -> int`.
- `resolution.py` — `BetInput`, `MatchResult`, `BetOutcome` (DTOs propios, nunca ORM);
  `resolve_bet(bet, result) -> BetOutcome` cubriendo `OUTCOME` y `GOAL_BAND`,
  devolviendo status y pago (`stake*odds` a 2 decimales; `0` si pierde; `stake` si VOID).
- `rules.py` — `is_open_for_betting(kickoff_at, now) -> bool` (borde cerrado:
  `now >= kickoff_at` es False); `validate_stake(stake) -> None`.
- `selection.py` — unión discriminada por `market`: `OutcomeSelection{pick: HOME|DRAW|AWAY}`,
  `GoalBandSelection{band: GoalBand, team_id: UUID|None}`. Valida **forma**, no pertenencia.

## Cómo correr los tests en el worktree
`backend/pyproject.toml` pertenece a la Phase 2 y no existe aquí. Usa:
`uv run --with pydantic --with pytest pytest backend/tests/engine/ -v`
No crees ni edites `backend/pyproject.toml`.

## Testing Plan (tests-first, es el DoD de la fase)
Escribe los tests **primero**, confirma que fallan, commitea ese estado fallando, y
luego implementa. Dos commits en esta fase, en ese orden.
1. **Barrido completo de los 10 000 pares `(1..100, 1..100)`** — se mantiene entero, es el
   requisito central y cuesta milisegundos:
   - `strength_home > strength_away` ⟹ `odds_home < odds_away`
   - `1/odds_home + 1/odds_draw + 1/odds_away > 1.0` en todo el dominio
   - ningún momio `< 1.01`
2. `compute_odds` determinista: dos llamadas iguales dan objetos iguales.
3. Puntuación: marcador exacto → 8; ganador acertado con marcador errado → 3; errado → 0.
4. `from_config({"exact_score": 10})` → 13 por marcador exacto y **sigue** dando 3 por
   ganador (merge por clave).
5. Franjas: minuto 90 con `is_stoppage=True` → `76-90+`; 46 → `46-60`; 45 → `31-45`.
6. `GOAL_BAND 0-15` con `team_id` del visitante **pierde** si el único gol de esa franja
   lo anotó el local.
7. `is_open_for_betting` es `False` en el instante exacto de `kickoff_at`.
8. `band: "20-40"` es rechazado por el modelo de selection.

# Quinielas de Fútbol

## Overview

Plataforma de quinielas de fútbol donde los usuarios pronostican resultados de partidos y acumulan **puntos** en una tabla de posiciones según qué tan acertados sean. Además de la quiniela clásica, los usuarios apuestan **créditos virtuales** sobre dos mercados: el resultado del partido (1X2) y la **franja de 15 minutos en la que caerá un gol**. El pago depende de un momio derivado de la fuerza relativa de los equipos: apostarle al equipo grande paga poco, apostarle al chico paga mucho.

El saldo es **crédito virtual no canjeable**: cada usuario arranca con un balance fijo, no hay depósitos ni retiros ni pasarela de pago. La mecánica de apuesta es idéntica a la de una casa real, pero el producto queda fuera del alcance de regulación de juego (sin KYC ni licencia). Cualquier requisito futuro de dinero real es un producto distinto y queda **explícitamente fuera de este PRD**.

El usuario objetivo es un aficionado que compite contra otros pronosticando; el segundo usuario es un **administrador** que da de alta temporadas, jornadas, equipos y partidos, y captura resultados —incluido el minuto de cada gol— porque en el MVP no hay proveedor externo de datos deportivos.

### Fuera de alcance (MVP)
- **Otros deportes.** El sistema es fútbol y solo fútbol: 1X2 con empate y franjas de gol de 15 minutos, ambos asumidos siempre. Se descartó el modelo multideporte a propósito, para no pagar la abstracción antes de necesitarla. Ver la tabla de riesgos para qué costaría reintroducirla.
- Dinero real, depósitos, retiros, KYC, antifraude, licencia de juego.
- Integración con API externa de resultados. El admin captura todo a mano.
- Ligas privadas / grupos entre amigos.
- Notificaciones push o email.
- Apuestas en vivo (in-play) o cash-out.

## Technical Context

- **Stack:** Python 3.13, FastAPI, Pydantic v2, SQLAlchemy 2.0 (declarativo tipado), Alembic, PostgreSQL 16, pytest, `mypy --strict`. Frontend en SvelteKit + TypeScript + Tailwind.
- **Arquitectura:** capas simples (`api` → `services` → `models`) con un núcleo de **funciones puras** aislado en `app/engine/`. Detalle en la sección [Arquitectura](#arquitectura).
- **Estructura:** monorepo con `backend/` y `web/` dentro del repo actual (`entrevista-proyecto`, hoy vacío salvo `pyproject.toml`).
- **Diseño:** el lenguaje visual se define primero en un canvas de **Claude Design** (Phase 1) y el frontend lo implementa; no se improvisa UI en el camino.
- **Auth:** email + contraseña, JWT de acceso, hash con Argon2. Sin OAuth en el MVP.
- **Entorno local:** `docker-compose` con PostgreSQL. Migraciones vía Alembic.
- **Convenciones:** type hints obligatorios; Pydantic para DTOs y para las entradas/salidas del motor; **sin mocking ni patching** — inyección por constructor y fixtures reales; comentarios solo cuando el código no puede expresar un porqué o una invariante.
- **Zona horaria:** todo se persiste y se compara en UTC (`TIMESTAMPTZ`). El frontend formatea a la zona del usuario.

## Arquitectura

Tres capas y un núcleo puro. No hay puertos, ni contenedor de dependencias, ni mappers entidad↔fila: los modelos de SQLAlchemy **son** el modelo de dominio. Lo único que se aísla con rigor es el motor de cálculo, porque es donde vive el valor del producto y donde los tests tienen que ser instantáneos.

```
app/api/          routers FastAPI, DTOs de request/response, códigos de estado
       │  llama
       ▼
app/services/     lógica transaccional: apostar, liquidar, cancelar, registrar
       │  usa                    │ persiste con
       ▼                         ▼
app/engine/  (PURO)         app/models/  (SQLAlchemy)
odds · bands · scoring · resolution
```

### Estructura de directorios

```
backend/
├── app/
│   ├── core/        # settings, seguridad (Argon2, JWT)
│   ├── db/          # engine, sesión, dependencia get_session
│   ├── models/      # SQLAlchemy: Team, Season, Round, Match, Goal, User, Bet, …
│   ├── schemas/     # DTOs Pydantic de la API
│   ├── engine/      # funciones puras, constantes y errores — el corazón del
│   │                #   producto, sin un solo import del resto de la app
│   ├── services/    # orquestación transaccional
│   └── api/         # routers
├── alembic/
├── scripts/
└── tests/
    ├── engine/      # puros, sin DB, instantáneos
    ├── services/    # contra PostgreSQL real, sin mocks
    └── api/         # integración por HTTP
```

### Reglas arquitectónicas (verificables, no aspiracionales)

- **A1 — Motor estéril.** Ningún módulo de `app/engine/` importa `sqlalchemy`, `fastapi` ni nada con I/O. Solo tipos estándar y Pydantic inmutable. Se verifica con `grep` en CI.
- **A2 — El motor no conoce el tiempo.** Nada en `app/engine/` ni en las reglas de cierre llama `datetime.now()`; el instante se recibe como parámetro. R3 se vuelve testeable sin dormir el test.
- **A3 — Transacción por servicio.** Un servicio abre y cierra una transacción; los routers no hacen `commit` y los modelos no se persisten a sí mismos.
- **A4 — Los errores cruzan hacia afuera.** Los servicios y el motor lanzan errores de dominio tipados (`app/engine/errors.py` — puro, sin dependencias); un único `exception_handler` los traduce a códigos HTTP. Ningún `HTTPException` dentro de `services/` ni de `engine/`.
- **A5 — Cero aritmética duplicada.** Momios, puntos y pagos se calculan **solo** en `app/engine/`. Un servicio que multiplique un stake por un momio está mal escrito.

### Trazabilidad entre reglas de negocio y código

| Regla | Vive en |
|---|---|
| R1 momios, R2 franjas, R8 puntuación | `app/engine/` — funciones puras |
| R3 cierre de apuestas | `app/engine/rules.py::is_open_for_betting(match, now)`, invocado por los servicios |
| R4 momio congelado | columna `bets.odds_snapshot` + `services/betting.py` |
| R5 ledger append-only | `services/wallet.py` — única puerta de escritura al ledger |
| R6 liquidación idempotente | `services/settlement.py` + bloqueo pesimista |
| R7 puntos vs créditos | dos rutas de código sin acoplamiento |
| R9 cancelación | `services/settlement.py::cancel_match` |

## Reglas de negocio canónicas

Estas reglas son la referencia única. Cualquier fase que las contradiga está mal implementada.

**R1 — Derivación de momios (determinista y pura).** Dadas `strength_home` y `strength_away` en `1..100`:
```
sh = strength_home * (1 + HOME_ADVANTAGE)     # HOME_ADVANTAGE = 0.10
sa = strength_away
p_home_raw = sh / (sh + sa)
p_draw = DRAW_BASE * (1 - abs(sh - sa) / (sh + sa))   # DRAW_BASE = 0.28
p_home  = (1 - p_draw) * p_home_raw
p_away  = (1 - p_draw) * (1 - p_home_raw)
odds_x  = max(MIN_ODDS, round((1 - MARGIN) / p_x, 2)) # MARGIN = 0.05, MIN_ODDS = 1.01
```
Invariante observable: si `strength_home > strength_away` entonces `odds_home < odds_away`. **Este es el requisito central del producto.**

**R2 — Mercado de franja de gol.** Franjas fijas: `0-15, 16-30, 31-45, 46-60, 61-75, 76-90+` (el `90+` absorbe el tiempo añadido). El usuario elige una franja y, opcionalmente, un equipo. Gana si **al menos un gol** cae dentro de esa franja (y lo anota ese equipo, si lo especificó). El momio de cada franja es configuración de temporada, con default `4.50`.

**R3 — Cierre de apuestas.** Un partido acepta apuestas y pronósticos hasta `match.kickoff_at`. A partir de ese instante toda escritura se rechaza con `409`. El cierre es una comparación de tiempo (`now >= kickoff_at`), no un estado persistido — no existe un status `LOCKED` que alguien tenga que acordarse de escribir. El `now` es siempre del servidor, nunca del cliente.

**R4 — Momio congelado.** El momio se calcula y se **persiste en la apuesta** (`odds_snapshot`) al momento de apostar. Un cambio posterior de `team.strength` no altera apuestas ya colocadas.

**R5 — Ledger.** Saldo inicial `SEED_CREDITS = 1000.00` al registrarse. Stake permitido de `MIN_STAKE = 10.00` a `MAX_STAKE = 500.00`, inclusive. Junto con las de R1 (`HOME_ADVANTAGE`, `DRAW_BASE`, `MARGIN`, `MIN_ODDS`), estas constantes viven **solo** en `app/engine/config.py` — un módulo puro sin dependencias, para que el motor no tenga que importar nada del resto de la app y ninguna fase elija números propios. El saldo es la suma del ledger, nunca un campo mutable suelto: `credit_transactions` es append-only, jamás se le hace `UPDATE` ni `DELETE`. El stake se debita al apostar; el pago se acredita al liquidar.

**R6 — Liquidación idempotente.** Cada apuesta se liquida exactamente una vez. La transición es `PENDING → WON | LOST | VOID` y es irreversible. Re-ejecutar la liquidación de un partido ya liquidado no produce movimientos adicionales.

**R7 — Puntos y créditos son ejes independientes.** Los puntos del ranking se otorgan por acierto del *pronóstico* y no dependen del stake. Los créditos se ganan o pierden por la *apuesta*. Un usuario puede pronosticar sin apostar.

**R8 — Puntuación (defaults configurables por temporada).** Acertar el ganador o el empate: `3` puntos. Acertar además el marcador exacto: `+5` (total `8`). Acertar franja de gol: `2`.

**R9 — Cancelación.** Si un partido se cancela, todas sus apuestas pasan a `VOID` y el stake se reembolsa íntegro vía ledger. No se otorgan puntos.

### Modelo de datos

```
Team (name, strength 1..100, crest_url)
Season (name, starts_on, ends_on, scoring_config JSONB) ──< Round (jornada) ──< Match ──< Goal (minute, is_stoppage, team)
User (email, password_hash, display_name, phone, contact_email, is_admin)
  ├──< CreditTransaction (kind: SEED|STAKE|PAYOUT|REFUND, amount NUMERIC(12,2))  — append-only
  ├──< Bet (match, market: OUTCOME|GOAL_BAND, selection JSONB, stake, odds_snapshot, status)
  └──< Prediction (match, predicted_home_score, predicted_away_score, points_awarded)  UNIQUE(user, match)
```

## Implementation Plan

*Cada fase lleva metadata de orquestación para `/build`. Las fases del mismo `parallel_group` corren simultáneamente; `depends_on` controla el orden entre grupos. Los `file_scope` de un mismo grupo nunca se solapan.*

**Grafo de ejecución:** `1,2,3 → 4,5 → 6,7 → 8,9`

### Phase 1: Diseño visual con Claude Design
<!-- orchestration:
parallel_group: 1
depends_on: []
agent_role: ui-designer
execution: main-session
skill: design
spec: docs/quinielas-futbol/design-prd.md
file_scope:
  - docs/quinielas-futbol/design/
-->
- **Description:** El lenguaje visual y los artboards de la aplicación se definen en un canvas de **Claude Design**, antes de escribir frontend. Corre en paralelo con todo el backend porque no toca código.
- **Especificación completa:** [`docs/quinielas-futbol/design-prd.md`](./design-prd.md) — es un documento independiente para que Alex lo trabaje en paralelo sin bloquearse contra este PRD.
- **Entregables que consumen las fases de frontend:**
  - `docs/quinielas-futbol/design/tokens.md` — paleta, tipografía, espaciado, radios, temas claro y oscuro.
  - La URL del canvas publicado, registrada en `docs/quinielas-futbol/design/README.md`.
- **Definition of Done (DoD):**
  - [ ] Se cumplieron todos los DoD de `design-prd.md`.
  - [ ] **Gate humano:** Alex aprobó el canvas. Sin esta aprobación, las Phases 8 y 9 no arrancan; la Phase 7 avanza igual porque solo consume `tokens.md`.

### Phase 2: Fundación — modelo de datos y andamiaje
<!-- orchestration:
parallel_group: 1
depends_on: []
agent_role: fastapi-developer
file_scope:
  - backend/app/core/
  - backend/app/db/
  - backend/app/models/
  - backend/alembic/
  - backend/tests/models/
  - backend/tests/conftest.py
  - backend/pyproject.toml
  - docker-compose.yml
-->
- **Description:** Esqueleto del backend y esquema completo de la base. Ninguna otra fase de backend arranca sin esto.
- **Tasks:**
  - [ ] Task 2.1: `backend/` con FastAPI, `core/config.py` (`pydantic-settings`) y `db/session.py` con `get_session` inyectable. `docker-compose.yml` con PostgreSQL 16.
  - [ ] Task 2.2: Dependencias en `pyproject.toml`: `fastapi`, `uvicorn`, `sqlalchemy`, `alembic`, `psycopg[binary]`, `pydantic-settings`, `pyjwt`, `argon2-cffi`, `pytest`, `pytest-asyncio`, `httpx`, `mypy`, `ruff`.
  - [ ] Task 2.4: Modelos: `Team(name, strength CHECK 1..100, crest_url)`, `Season(name, starts_on, ends_on, scoring_config JSONB, status)`, `Round(season_id, number, name, opens_at, closes_at)`.
  - [ ] Task 2.5: `Match(round_id, home_team_id, away_team_id, kickoff_at TIMESTAMPTZ, status ENUM[SCHEDULED,FINISHED,CANCELLED], home_score, away_score, settled_at)` y `Goal(match_id, team_id, minute, is_stoppage)`.
  - [ ] Task 2.6: `User(email UNIQUE, password_hash, display_name, phone, contact_email, is_admin, created_at)` y `CreditTransaction(user_id, kind ENUM[SEED,STAKE,PAYOUT,REFUND], amount NUMERIC(12,2), bet_id NULL, created_at)`.
  - [ ] Task 2.7: `Prediction(user_id, match_id, predicted_home_score, predicted_away_score, points_awarded NULL)` con `UNIQUE(user_id, match_id)`; `Bet(user_id, match_id, market ENUM[OUTCOME,GOAL_BAND], selection JSONB, stake NUMERIC(12,2), odds_snapshot NUMERIC(6,2), status ENUM[PENDING,WON,LOST,VOID], settled_at NULL)`.
  - [ ] Task 2.8: Migración inicial de Alembic. Índices en `matches(round_id, kickoff_at)`, `bets(match_id, status)`, `credit_transactions(user_id)`.
  - [ ] Task 2.9: `tests/conftest.py` con fixture de base por test (transacción con rollback) y fixture de cliente HTTP. Sin mocking de la DB.
- **Definition of Done (DoD):**
  - [ ] `docker compose up -d db && alembic upgrade head` corre limpio desde cero; salida mostrada.
  - [ ] `alembic downgrade base && alembic upgrade head` es reversible sin error.
  - [ ] Test: `INSERT` de `Team` con `strength = 0` o `101` es rechazado por el CHECK de la base, no solo por Python.
  - [ ] Test: `Prediction` duplicado para `(user_id, match_id)` viola el UNIQUE.
  - [ ] Toda columna de dinero es `NUMERIC(12,2)`: `grep -rn "Float\|DOUBLE" backend/app/models/` no devuelve coincidencias.
  - [ ] `mypy --strict backend/app` pasa; salida mostrada.
  - [ ] `pytest backend/tests/models/` pasa con salida real, no un resumen.

### Phase 3: Motor de momios, franjas y puntuación (puro, tests-first)
<!-- orchestration:
parallel_group: 1
depends_on: []
agent_role: python-pro
file_scope:
  - backend/app/engine/
  - backend/tests/engine/
-->
- **Description:** El corazón del producto: funciones puras sobre tipos estándar y modelos Pydantic `frozen`, sin base de datos ni I/O. **Se escriben los tests primero, se confirma que fallan, se commitean, y luego se implementa.** Corre en paralelo con la Phase 2 porque no importa nada de ella: recibe `int`, `Decimal` y DTOs propios, y define sus propias constantes. Es la única fase que puede escribirse contra un repo vacío.
- **Tasks:**
  - [ ] Task 3.1: Escribir `tests/engine/test_odds.py` **antes** de implementar, cubriendo los invariantes de R1.
  - [ ] Task 3.2: `engine/errors.py` con los errores de dominio: `BettingClosed`, `InsufficientCredits`, `StakeOutOfRange`, `AlreadySettled`, `InvalidSelection`, `NotFound`. Ninguno hereda de `HTTPException` (A4). Viven aquí porque `engine/` es el paquete sin dependencias: todo lo demás puede importarlo.
  - [ ] Task 3.3: `engine/config.py` con **todas** las constantes de negocio (`HOME_ADVANTAGE`, `DRAW_BASE`, `MARGIN`, `MIN_ODDS`, `SEED_CREDITS`, `MIN_STAKE`, `MAX_STAKE`) y los defaults de `ScoringRules`. Es un módulo puro sin imports del resto de la app, y es la única fuente de esos números.
  - [ ] Task 3.4: `engine/odds.py`: `compute_odds(strength_home: int, strength_away: int, config: OddsConfig) -> MatchOdds` según R1. `OddsConfig` y `MatchOdds` son Pydantic `frozen=True`.
  - [ ] Task 3.5: `engine/bands.py`: enum `GoalBand` con las seis franjas de R2 y `band_for_minute(minute: int, is_stoppage: bool) -> GoalBand` (el tiempo añadido cae en `76-90+`).
  - [ ] Task 3.6: `engine/scoring.py`: `score_prediction(predicted: Score, actual: Score, rules: ScoringRules) -> int` según R8. `ScoringRules.from_config(raw: dict | None) -> ScoringRules` construye las reglas desde el `scoring_config` de la temporada, cayendo a los defaults de `engine/config.py` para cada clave ausente. Es el único puente entre el JSONB y el motor.
  - [ ] Task 3.7: `engine/resolution.py`: `resolve_bet(bet: BetInput, result: MatchResult) -> BetOutcome`. `BetInput` y `MatchResult` son DTOs propios del motor que el servicio construye a partir de las filas ORM; el motor **nunca** recibe un objeto SQLAlchemy. devolviendo `WON | LOST | VOID` y el pago (`stake * odds_snapshot`, 2 decimales; `0` si pierde; `stake` si `VOID`). Cubre los dos mercados.
  - [ ] Task 3.8: `engine/rules.py`: `is_open_for_betting(kickoff_at, now) -> bool` (R3) y `validate_stake(stake) -> None` (R5). El `now` siempre entra por parámetro (A2).
  - [ ] Task 3.9: `engine/selection.py`: modelos Pydantic discriminados por `market` que validan la **forma** de la `selection` — `OUTCOME` acepta `HOME|DRAW|AWAY`; `GOAL_BAND` acepta una de las seis franjas y un `team_id` opcional (UUID o `None`). El motor valida forma, no pertenencia: comprobar que ese `team_id` **juega ese partido** requiere la base y vive en `services/betting.py` (Task 6.4).
  - [ ] Task 3.10: Barrido de propiedad sobre los 10 000 pares `(1..100, 1..100)`.
- **Definition of Done (DoD):**
  - [ ] Los tests se commitearon **fallando** antes de la implementación (visible en el historial de git).
  - [ ] Test: para todo par con `strength_home > strength_away`, `odds_home < odds_away`. Barrido completo de los 10 000 pares, no un caso puntual. **Es el requisito central del producto.**
  - [ ] Test: `1/odds_home + 1/odds_draw + 1/odds_away > 1.0` en todo el dominio `1..100` (existe margen de la casa). Nota: el clamp `MIN_ODDS` erosiona el margen en los desbalances extremos (`100` vs `1` da ~`1.005`); si el barrido encuentra un caso `<= 1.0`, subir `MIN_ODDS` en vez de relajar el test.
  - [ ] Test: ningún momio es menor a `1.01`.
  - [ ] Test: `compute_odds` es determinista — dos llamadas con la misma entrada devuelven objetos iguales.
  - [ ] Test: marcador exacto acertado otorga `8` puntos con la config default; ganador acertado con marcador errado otorga `3`; ganador errado otorga `0`.
  - [ ] Test: gol al minuto `90` con `is_stoppage=True` cae en `76-90+`; gol al `46` cae en `46-60`; gol al `45` cae en `31-45`.
  - [ ] Test: apuesta de franja `0-15` con `team_id` del visitante **pierde** si el único gol de esa franja lo anotó el local.
  - [ ] Test: `is_open_for_betting` devuelve `False` en el instante exacto de `kickoff_at` (el borde es cerrado).
  - [ ] Test: `band: "20-40"` es rechazado por el modelo de `selection`. La pertenencia del `team_id` al partido **no** se prueba aquí: es un test de la Phase 6.
  - [ ] `grep -rnE "sqlalchemy|fastapi|datetime\.now|utcnow|from app\." backend/app/engine/` no devuelve coincidencias — el motor no importa nada del resto de la app (A1, A2), por eso puede construirse en paralelo con la Phase 2.
  - [ ] Las constantes de negocio existen en un solo archivo: `grep -rn "HOME_ADVANTAGE\|SEED_CREDITS\|MIN_STAKE" backend/app/` solo las define en `engine/config.py`.
  - [ ] `pytest backend/tests/engine/ -v` pasa en menos de 2 segundos, con PostgreSQL **detenido**; salida mostrada.

### Phase 4: Cuentas, perfil y wallet
<!-- orchestration:
parallel_group: 2
depends_on: ["Phase 2"]
agent_role: fastapi-developer
file_scope:
  - backend/app/core/security.py
  - backend/app/services/users.py
  - backend/app/services/wallet.py
  - backend/app/schemas/user.py
  - backend/app/schemas/wallet.py
  - backend/app/api/auth.py
  - backend/app/api/users.py
  - backend/app/api/wallet.py
  - backend/app/api/exception_handlers.py
  - backend/app/main.py
  - backend/tests/services/test_wallet.py
  - backend/tests/api/test_auth.py
-->
- **Description:** Registro, login, el perfil donde el usuario captura sus datos de contacto, y el **ledger de créditos**. El wallet va aquí y no en la fase de apuestas a propósito: es la pieza donde un bug significa saldo inventado o desaparecido, y merece sus propios tests aislados de la lógica de juego.
- **Tasks:**
  - [ ] Task 4.1: `core/security.py`: hash Argon2, emisión y verificación de JWT, dependencias `require_current_user` y `require_admin`.
  - [ ] Task 4.2: `app/main.py` con la app FastAPI y `api/exception_handlers.py` con un **único** handler que importa desde `engine/errors.py` que traduce los errores de `engine/errors.py` a HTTP (A4): `BettingClosed → 409`, `InsufficientCredits → 402`, `StakeOutOfRange → 422`, `InvalidSelection → 422`, `AlreadySettled → 409`, `NotFound → 404`.
  - [ ] Task 4.3: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/users/me`, `PATCH /api/v1/users/me` (display_name, teléfono, email de contacto).
  - [ ] Task 4.4: Al registrar, insertar la `CreditTransaction` de tipo `SEED` con `SEED_CREDITS` en la **misma transacción** que el `INSERT` de `User`.
  - [ ] Task 4.5: `services/wallet.py` — `get_balance(session, user_id) -> Decimal` como `SUM(amount)` del ledger, y `post_transaction(...)`. Es la **única** puerta de escritura al ledger en todo el código.
  - [ ] Task 4.6: `debit(...)` rechaza si el balance resultante sería negativo, lanzando `InsufficientCredits`. Sin fallback automático ni reintento silencioso.
  - [ ] Task 4.7: Bloqueo pesimista (`SELECT ... FOR UPDATE` sobre la fila del usuario) al debitar, para que dos apuestas concurrentes no sobregiren.
  - [ ] Task 4.8: `GET /api/v1/wallet` (balance) y `GET /api/v1/wallet/transactions` (historial paginado).
  - [ ] Task 4.9: `scripts/create_admin.py` para promover una cuenta a `is_admin`.
- **Definition of Done (DoD):**
  - [ ] Test: registro devuelve `201`; un segundo registro con el mismo email devuelve `409`.
  - [ ] Test: login válido devuelve un JWT que `GET /users/me` acepta; contraseña errada devuelve `401`; sin token, `401`.
  - [ ] Test: tras el registro el usuario tiene exactamente una transacción `SEED` y balance `1000.00`.
  - [ ] Test: si el `INSERT` de `User` falla, no queda ninguna `CreditTransaction` huérfana.
  - [ ] Test: un usuario sin `is_admin` recibe `403` en un endpoint protegido por `require_admin`.
  - [ ] Test: `get_balance` sobre `SEED 1000 + STAKE -50 + PAYOUT 150` devuelve exactamente `Decimal("1100.00")`.
  - [ ] Test: debitar más que el balance lanza `InsufficientCredits`, devuelve `402` y **no** inserta ninguna transacción.
  - [ ] Test de concurrencia real contra PostgreSQL: dos débitos simultáneos de `600` sobre un balance de `1000` — exactamente uno tiene éxito y el balance nunca queda negativo.
  - [ ] El `password_hash` no aparece en ninguna respuesta de la API (verificado en test).
  - [ ] `grep -rnE "UPDATE|DELETE" backend/app/services/wallet.py` no muestra escrituras destructivas sobre `credit_transactions` (R5), y ningún otro módulo escribe en esa tabla.
  - [ ] `grep -rn "float(" backend/app/services/wallet.py` no devuelve coincidencias.

### Phase 5: API de administración — catálogo
<!-- orchestration:
parallel_group: 2
depends_on: ["Phase 2"]
agent_role: fastapi-developer
file_scope:
  - backend/app/services/catalog.py
  - backend/app/schemas/catalog.py
  - backend/app/api/admin/
  - backend/scripts/seed_demo.py
  - backend/tests/api/test_admin_catalog.py
-->
- **Description:** Todo lo que el admin necesita para armar una temporada. La captura de resultados **no** va aquí: vive en la Phase 6 junto a la liquidación, porque son la misma operación transaccional.
- **Tasks:**
  - [ ] Task 5.1: CRUD `/api/v1/admin/teams` (con `strength`), `/admin/seasons`, `/admin/rounds`, `/admin/matches`. Todo bajo `require_admin`.
  - [ ] Task 5.2: `PATCH /api/v1/admin/seasons/{id}/scoring` para editar `scoring_config` (puntos por acierto y momio por franja).
  - [ ] Task 5.3: `GET /api/v1/admin/teams/{id}/odds-preview?opponent_strength=N` — devuelve los momios que resultarían, para alimentar el slider del panel de admin.
  - [ ] Task 5.4: Validaciones: los dos equipos de un partido son distintos; `kickoff_at` cae dentro de la ventana de la jornada; `strength` entre 1 y 100.
  - [ ] Task 5.5: `scripts/seed_demo.py` — una temporada con dos jornadas, ocho equipos con `strength` deliberadamente dispares (p. ej. `92` y `24`) y partidos en el futuro, para que el sistema se pueda navegar de inmediato.
- **Definition of Done (DoD):**
  - [ ] Test: crear un partido con el mismo equipo de local y visitante devuelve `422`.
  - [ ] Test: crear un partido con `kickoff_at` fuera de la ventana de su jornada devuelve `422`.
  - [ ] Test: `strength = 0` o `101` devuelve `422`.
  - [ ] Test: un usuario no-admin recibe `403` en todos los endpoints de `/admin/`.
  - [ ] Test: `odds-preview` de un equipo con `strength=92` contra `opponent_strength=24` devuelve `odds_home < odds_away`.
  - [ ] `python backend/scripts/seed_demo.py` corre y deja una temporada navegable; salida mostrada.

### Phase 6: Juego — pronósticos, apuestas, resultados y liquidación
<!-- orchestration:
parallel_group: 3
depends_on: ["Phase 3", "Phase 4", "Phase 5"]
agent_role: fastapi-developer
file_scope:
  - backend/app/services/betting.py
  - backend/app/services/results.py
  - backend/app/services/settlement.py
  - backend/app/services/leaderboard.py
  - backend/app/schemas/betting.py
  - backend/app/api/matches.py
  - backend/app/api/bets.py
  - backend/app/api/leaderboard.py
  - backend/app/api/admin/results.py
  - backend/tests/services/test_settlement.py
  - backend/tests/api/test_game.py
-->
- **Description:** El ciclo completo del juego: el usuario pronostica y apuesta, el admin captura el resultado con los minutos de cada gol, y el sistema liquida pagos y puntos. Es la fase más pesada del backend y donde se concentran los tests que importan. Toda la aritmética se delega a `app/engine/` (A5); estos servicios solo orquestan y persisten.
- **Tasks:**
  - [ ] Task 6.1: `GET /api/v1/matches/upcoming` — partidos futuros con equipos, `kickoff_at`, momios de resultado calculados en vivo, momios de franja, y el pronóstico y apuestas propias del usuario si existen.
  - [ ] Task 6.2: `PUT /api/v1/matches/{id}/prediction` — crea o reemplaza el pronóstico de marcador; idempotente sobre `(user_id, match_id)`.
  - [ ] Task 6.3: `POST /api/v1/matches/{id}/bets` con el DTO discriminado de `engine/selection.py`: `OUTCOME` (`{pick}`) o `GOAL_BAND` (`{band, team_id?}`).
  - [ ] Task 6.4: `services/betting.py::place_bet` — en **una sola transacción**: verifica R3 con el `now` del servidor, valida el stake (R5), valida la forma de la `selection` con `engine/selection.py` y **la pertenencia del `team_id` al partido** (`InvalidSelection` si no juega), calcula el momio con `engine/odds.py`, lo congela en `odds_snapshot` (R4), debita vía `services/wallet.py` y crea el `Bet` en `PENDING`.
  - [ ] Task 6.5: `PUT /api/v1/admin/matches/{id}/result` con `{home_score, away_score, goals: [{team_id, minute, is_stoppage}]}` — valida que los goles cuadran con el marcador y que cada `team_id` juega ese partido; persiste los `Goal`, deja el partido `FINISHED` y dispara la liquidación en la misma transacción.
  - [ ] Task 6.6: `services/settlement.py::settle_match` — carga apuestas `PENDING` con `SELECT ... FOR UPDATE`, delega a `engine/resolution.py`, acredita pagos, puntúa pronósticos con `engine/scoring.py` usando `ScoringRules.from_config(season.scoring_config)` y marca `settled_at`. Idempotente (R6).
  - [ ] Task 6.7: `cancel_match` (R9) y `POST /api/v1/admin/matches/{id}/settle` como reintento manual explícito.
  - [ ] Task 6.8: `GET /api/v1/bets` (propias, filtrables por estado), `GET /api/v1/seasons/{id}/leaderboard` (orden por puntos; desempate por marcadores exactos, luego por balance) y `GET /api/v1/rounds/{id}/results`.
- **Definition of Done (DoD):**
  - [ ] Test: apostar `100` con balance `1000` deja el balance en `900` y crea un `Bet` `PENDING` con `odds_snapshot` no nulo.
  - [ ] Test: apostar o pronosticar sobre un partido cuyo `kickoff_at` ya pasó devuelve `409` y el balance no cambia.
  - [ ] Test: stake `5` o `501` devuelve `422`; balance insuficiente devuelve `402` sin crear `Bet` ni transacción.
  - [ ] Test de atomicidad, **ambas direcciones**: (a) con saldo insuficiente no se crea ni `Bet` ni asiento `STAKE`; (b) si la creación del `Bet` falla tras el débito, el asiento `STAKE` tampoco persiste. La segunda es la dirección que roba créditos en silencio.
  - [ ] Test **crítico de R4**: se coloca una apuesta, el admin cambia `team.strength`, y el `odds_snapshot` de la apuesta existente permanece idéntico.
  - [ ] Test: `PUT .../prediction` dos veces deja exactamente una fila, con los valores de la segunda llamada.
  - [ ] Test: `GET /matches/upcoming` de un partido con `strength_home=90, strength_away=30` devuelve `odds_home < odds_away`.
  - [ ] Test: capturar resultado `2-1` con solo 2 goles en el arreglo devuelve `422` y no persiste nada; con un `team_id` ajeno al partido, `422`.
  - [ ] Test: apostar `GOAL_BAND` con un `team_id` de un equipo que no juega ese partido devuelve `422` y no debita nada.
  - [ ] Test: una temporada con `scoring_config = {"exact_score": 10}` otorga `13` puntos por marcador exacto y sigue otorgando `3` por ganador acertado — el JSONB sobrescribe clave por clave, no bloque completo.
  - [ ] Test end-to-end por HTTP: partido `2-1` con goles al `12` y `70` (local) y `55` (visitante). Un usuario apuesta `HOME`, otro la franja `61-75`. Ambos ganan y su balance sube exactamente `stake * odds_snapshot`.
  - [ ] Test: quien apostó la franja `0-15` con el `team_id` del visitante **pierde** (hubo gol en esa franja, pero del local).
  - [ ] Test **crítico de R6**: invocar `settle_match` tres veces produce exactamente el mismo balance y el mismo número de transacciones que invocarla una vez.
  - [ ] Test de concurrencia real: dos liquidaciones simultáneas del mismo partido producen un solo conjunto de pagos.
  - [ ] Test **R7**: un usuario que solo pronosticó y **no** apostó recibe sus puntos y aparece en el leaderboard, con el balance intacto.
  - [ ] Test **R7**: dos usuarios con el mismo pronóstico acertado pero stakes de `10` y `500` reciben los mismos puntos y difieren solo en créditos.
  - [ ] Test **R9**: cancelar un partido con dos apuestas las deja en `VOID`, reembolsa el stake exacto y no otorga puntos.
  - [ ] Test: el leaderboard ordena por puntos y aplica el desempate por marcadores exactos.
  - [ ] `grep -rnE "\* *odds|HOME_ADVANTAGE|DRAW_BASE" backend/app/services/` no devuelve coincidencias — ningún servicio hace aritmética de momios (A5).
  - [ ] `grep -rn "HTTPException" backend/app/services/ backend/app/engine/` no devuelve coincidencias (A4).

### Phase 7: Frontend — fundación, sistema de diseño y auth
<!-- orchestration:
parallel_group: 3
depends_on: ["Phase 4"]
agent_role: typescript-pro
file_scope:
  - web/src/lib/
  - web/src/app.css
  - web/src/routes/+layout.svelte
  - web/src/routes/(auth)/
  - web/package.json
  - web/tailwind.config.ts
  - web/svelte.config.js
-->
- **Description:** Base de SvelteKit, cliente API tipado y pantallas de cuenta. Depende de la Phase 4 porque necesita el `openapi.json` con las rutas de auth montadas. Consume `tokens.md` de la Phase 1, pero **no** el gate de aprobación: si el canvas todavía no está aprobado, el agente arranca con las Tasks 7.1, 7.3, 7.4 y 7.5 y deja 7.2 y 7.6 para cuando `tokens.md` exista.
- **Nota de agente:** no hay especialista en Svelte en el registro, así que se asigna `typescript-pro`; el agente **debe** consultar el MCP oficial de Svelte antes de escribir componentes y volver a validarlos con él al terminar.
- **Tasks:**
  - [ ] Task 7.1: Inicializar SvelteKit con TypeScript y Tailwind en `web/`.
  - [ ] Task 7.2: Traducir `docs/quinielas-futbol/design/tokens.md` a `tailwind.config.ts` y `app.css` — paleta, tipografía con cifras tabulares, espaciado, radios, variables de tema claro y oscuro.
  - [ ] Task 7.3: Generar tipos TS desde el `openapi.json` del backend corriendo (`openapi-typescript`), como script de `package.json`. Prohibido escribir tipos de API a mano.
  - [ ] Task 7.4: `lib/api/client.ts` — fetch tipado, inyección del JWT y mapeo de cada código de error del backend (`402`, `409`, `422`) a un mensaje legible. Ningún fallo silencioso.
  - [ ] Task 7.5: Store de sesión, guard de rutas y redirección a login en `401`. Pantallas de registro, login y perfil; barra superior persistente con el balance.
  - [ ] Task 7.6: Componentes base del sistema de diseño (`Button`, `Card`, `Money`, `OddsChip`, `StatusBadge`) según los artboards de la Phase 1.
- **Definition of Done (DoD):**
  - [ ] `npm run build` y `npm run check` pasan sin errores de tipo; salida mostrada.
  - [ ] Los tipos del cliente se generaron desde el OpenAPI real, no a mano.
  - [ ] Los valores de `tailwind.config.ts` coinciden uno a uno con `tokens.md`; cualquier color fuera de los tokens es un fallo.
  - [ ] Flujo manual con screenshots: registrarse → ver balance `1000` en la barra → cerrar sesión → login → el balance persiste.
  - [ ] Un `401` de la API redirige a login en vez de romper la pantalla.
  - [ ] Los componentes se validaron con el MCP de Svelte y no quedan advertencias abiertas.

### Phase 8: Frontend — panel del usuario
<!-- orchestration:
parallel_group: 4
depends_on: ["Phase 1", "Phase 6", "Phase 7"]
agent_role: typescript-pro
file_scope:
  - web/src/routes/(app)/
-->
- **Description:** La pantalla que describió Alex: próximos partidos, pronóstico de marcador, apuesta al ganador y apuesta a la franja del gol, más ranking e historial. Implementa los artboards de `design-prd.md`.
- **Tasks:**
  - [ ] Task 8.1: `/partidos` — próximos partidos con equipos, hora local, cuenta regresiva al cierre y los momios como chips seleccionables.
  - [ ] Task 8.2: Formulario de pronóstico de marcador, con el pronóstico guardado precargado.
  - [ ] Task 8.3: Formulario de apuesta al resultado: selección, monto y **ganancia potencial calculada en vivo** (`stake * odds`) antes de confirmar.
  - [ ] Task 8.4: Sección de apuesta por franja de gol sobre la línea de tiempo del artboard correspondiente, con equipo opcional.
  - [ ] Task 8.5: `/mis-apuestas` — historial con estado, momio congelado y pago; `/saldo` — movimientos del ledger.
  - [ ] Task 8.6: `/ranking` — tabla de posiciones de la temporada.
  - [ ] Task 8.7: Los partidos cerrados se muestran en solo lectura, con los formularios deshabilitados; estados vacíos según el artboard de errores.
- **Definition of Done (DoD):**
  - [ ] Verificación manual con screenshots del flujo completo: pronosticar → apostar al resultado → apostar a la franja → el balance baja por el stake.
  - [ ] La ganancia potencial mostrada coincide exactamente con `stake * odds` de la respuesta del backend.
  - [ ] En un partido con `kickoff_at` pasado, ambos formularios aparecen deshabilitados (y la API los rechazaría igual).
  - [ ] Apostar por encima del balance muestra el mensaje del artboard de errores, no un stack trace.
  - [ ] Tras liquidar un partido, `/mis-apuestas` refleja `WON`/`LOST` con el pago correcto y `/ranking` muestra los puntos.
  - [ ] Comparación lado a lado con los artboards: espaciado, tipografía y estados coinciden.
  - [ ] `npm run check` pasa.

### Phase 9: Frontend — panel de administración
<!-- orchestration:
parallel_group: 4
depends_on: ["Phase 1", "Phase 5", "Phase 6", "Phase 7"]
agent_role: typescript-pro
file_scope:
  - web/src/routes/admin/
-->
- **Description:** La interfaz mínima pero completa para operar sin tocar la base ni `curl`. Corre en paralelo con la Phase 8 porque no comparte archivos.
- **Tasks:**
  - [ ] Task 9.1: CRUD de equipos con el `strength` como slider `1..100` que consulta `odds-preview` y muestra en vivo el momio resultante contra un rival de referencia.
  - [ ] Task 9.2: CRUD de temporadas y jornadas; editor de `scoring_config`.
  - [ ] Task 9.3: Alta de partidos dentro de una jornada.
  - [ ] Task 9.4: Captura de resultado: marcador más una lista editable de goles (equipo, minuto, tiempo añadido), con validación en cliente de que los goles cuadran con el marcador.
  - [ ] Task 9.5: Cancelar partido y reintentar liquidación, ambas con confirmación explícita.
- **Definition of Done (DoD):**
  - [ ] Verificación manual con screenshots: crear temporada → jornada → equipos con strengths dispares → partido → capturar resultado con minutos de gol → ver las apuestas liquidadas.
  - [ ] El slider de `strength` muestra el momio y se ve **caer** al subir la fuerza — la mecánica central del producto queda visible para el admin.
  - [ ] El editor de resultado impide enviar si los goles no cuadran con el marcador, y el backend lo rechaza igualmente si se fuerza.
  - [ ] Un usuario no-admin que navega a `/admin` es rechazado.
  - [ ] `npm run check` pasa.

## Gates transversales

No son fases: son condiciones que se verifican al cerrar cada grupo paralelo.

- [ ] `mypy --strict backend/app` verde.
- [ ] `pytest backend/tests/engine` corre **con PostgreSQL detenido** y pasa en menos de 2 segundos. Si necesita la base, A1 se rompió.
- [ ] Los greps de A1, A4 y A5 no devuelven coincidencias.
- [ ] Ninguna prueba se editó para forzar un pase. Los tests son la fuente de verdad.
- [ ] Cada DoD se cierra mostrando el comando y su salida real, nunca un resumen.
- [ ] **Gate humano:** el canvas de la Phase 1 está aprobado antes de que arranquen las Phases 8 y 9.

## Riesgos y decisiones abiertas

| Riesgo / decisión | Postura en el MVP |
|---|---|
| Alex pidió "apostar dinero" y se resolvió como crédito virtual | Confirmado explícitamente. Dinero real sería otro producto: pagos, retiros, KYC, licencia y antifraude. No se construyen ganchos especulativos ahora. |
| Se descartó la arquitectura hexagonal | Decisión de Alex tras ver el costo. Se conserva lo barato y valioso —el motor puro aislado en `app/engine/`, verificado con `grep`— y se tira la ceremonia: sin puertos, sin contenedor de DI, sin mappers entidad↔fila. El precio es que los servicios se prueban contra PostgreSQL real en vez de fakes en memoria; a cambio hay ~40% menos código de andamiaje. |
| Solo fútbol | Decisión de Alex, para optimizar la lógica. El empate y las franjas de 15 minutos se asumen siempre y **no** hay entidad `Sport` ni flags de capacidad. Reintroducir multideporte después cuesta: tabla `sports`, dos flags (`allows_draw`, `has_timed_goals` — son preguntas independientes: el basquetbol tiene reloj y no admite empate; el cricket al revés), `sport_id` en `Team` y `Season`, y ramas en `compute_odds` y en la validación de mercados. Contenido, pero no trivial: hay que hacerlo a conciencia o no hacerlo. |
| Momios derivados de `strength` en vez de momios por partido | Elegido por Alex. R1 vive en una función pura, así que sustituirla por momios capturados a mano es un cambio local. |
| Sin proveedor externo de resultados | El admin captura todo a mano. Añadir un proveedor después es un módulo nuevo que escribe en `matches` y `goals`; el resto del sistema no se entera. |
| Liquidación síncrona dentro del request de captura de resultado | Aceptable para el volumen del MVP. `settle_match` es una función de servicio independiente del transporte, así que moverla a background no toca lógica. `POST /settle` ya existe como reintento. |
| El canvas de diseño se aprueba antes de que exista el frontend | La Phase 1 tiene gate humano. Reimplementar pantallas cuesta más que iterar artboards. La Phase 7 se diseñó para no bloquearse: solo dos de sus seis tareas dependen del canvas. |
| No hay agente especialista en Svelte | Se usa `typescript-pro` con obligación de consultar el MCP oficial de Svelte antes y después de escribir componentes. |

# Spec — Phase 4: Cuentas, perfil y wallet

## Goal
Registro, login, perfil, y el **ledger de créditos** — la pieza donde un bug significa
saldo inventado o desaparecido. Monta también la app FastAPI y el traductor único de
errores de dominio a HTTP.

## Entorno
`DATABASE_URL=postgresql+psycopg://quinielas:quinielas@localhost:5432/quinielas_p4`
(base propia para no chocar con la Phase 5, que corre en paralelo).
El esquema ya existe vía Alembic (Phase 2). El motor puro ya existe en `app/engine/`
(Phase 3) — **importa de ahí, no reimplementes números ni errores**.

## Decisión de arquitectura: `main.py` pre-registra los routers downstream
`app/main.py` es de esta fase, pero las Phases 5 y 6 añaden routers y **no** tienen
`main.py` en su scope. Sin esto, esas fases entregarían código que nadie llama.
Por tanto `main.py` incluye los routers de las fases posteriores con un include
tolerante que salta el módulo que aún no existe:

```python
_ROUTERS = [
    ("app.api.auth", "router"),
    ("app.api.users", "router"),
    ("app.api.wallet", "router"),
    ("app.api.admin.catalog", "router"),    # Phase 5
    ("app.api.matches", "router"),          # Phase 6
    ("app.api.bets", "router"),             # Phase 6
    ("app.api.leaderboard", "router"),      # Phase 6
    ("app.api.admin.results", "router"),    # Phase 6
]
```

Cada entrada se importa con `importlib`; `ModuleNotFoundError` de *ese* módulo se ignora.
Es el único lugar del código con tolerancia a módulos ausentes, y existe solo para que
las fases paralelas queden cableadas al fusionarse.

## Implementation Steps
1. `core/security.py` — Argon2 (`argon2-cffi`) `hash_password`/`verify_password`;
   `create_access_token`/`decode_access_token` con PyJWT; dependencias
   `require_current_user` y `require_admin` (403 si no es admin).
2. `api/exception_handlers.py` — **un único** handler registrado sobre `DomainError`
   de `app/engine/errors.py`, con el mapa: `BettingClosed→409`,
   `InsufficientCredits→402`, `StakeOutOfRange→422`, `InvalidSelection→422`,
   `AlreadySettled→409`, `NotFound→404`. Cero `HTTPException` en services/ y engine/.
3. `app/main.py` — app FastAPI, handler registrado, includes tolerantes de arriba.
4. `services/users.py` — `register(session, ...)` inserta `User` **y** la
   `CreditTransaction` `SEED` de `SEED_CREDITS` en la **misma** transacción;
   email duplicado → 409. `authenticate(...)`, `update_profile(...)`.
5. `services/wallet.py` — **única puerta de escritura al ledger de todo el código**:
   - `get_balance(session, user_id) -> Decimal` = `SUM(amount)`, `Decimal("0.00")` si vacío.
   - `post_transaction(session, user_id, kind, amount, bet_id=None) -> CreditTransaction`
   - `debit(session, user_id, amount, bet_id=None)` — hace `SELECT ... FOR UPDATE`
     sobre la fila del `User` **antes** de leer el balance (bloqueo pesimista, para que
     dos apuestas concurrentes no sobregiren), y lanza `InsufficientCredits` si el
     balance resultante sería negativo. Sin fallback ni reintento silencioso.
   - `credit(session, user_id, amount, kind, bet_id=None)`
   Nunca `UPDATE` ni `DELETE` sobre `credit_transactions`. Nunca `float()`.
6. `schemas/user.py`, `schemas/wallet.py` — DTOs Pydantic. `password_hash` **jamás**
   sale en una respuesta: los schemas de salida no lo declaran.
7. Endpoints: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`,
   `GET|PATCH /api/v1/users/me`, `GET /api/v1/wallet`,
   `GET /api/v1/wallet/transactions` (paginado).
8. `scripts/create_admin.py` — promueve una cuenta a `is_admin` por email.

## Edge Cases
- El `SEED` y el `User` van en una transacción: si el INSERT de `User` falla no puede
  quedar una `CreditTransaction` huérfana.
- `get_balance` sobre `SEED 1000 + STAKE -50 + PAYOUT 150` debe dar exactamente
  `Decimal("1100.00")` — sin pasar por float en ningún punto.

## Testing Plan (ligero — decisión explícita de Alex)
`tests/api/test_auth.py`:
1. Registro → 201; segundo registro con el mismo email → 409.
2. Login válido → JWT que `GET /users/me` acepta; contraseña errada → 401; sin token → 401.
3. `password_hash` no aparece en ninguna respuesta.
4. No-admin en endpoint con `require_admin` → 403.

`tests/services/test_wallet.py`:
5. Tras registro: exactamente una transacción `SEED` y balance `Decimal("1000.00")`.
6. `get_balance` con `SEED 1000 + STAKE -50 + PAYOUT 150` → `Decimal("1100.00")`.
7. Debitar más que el balance → `InsufficientCredits`, y **no** inserta transacción.

Los tests de concurrencia real y de transacción huérfana quedan **fuera** por tiempo.
El `SELECT ... FOR UPDATE` se implementa igual: es una línea y es la que evita el
sobregiro en producción.

# Quinielas de Fútbol

Plataforma donde los usuarios pronostican marcadores para acumular **puntos** en un ranking
y apuestan **créditos virtuales** en dos mercados: el resultado del partido (1X2) y la
**franja de 15 minutos en la que caerá un gol**. El momio se deriva de la fuerza relativa de
los equipos: apostarle al grande paga poco, al chico paga mucho.

Los créditos son virtuales y no canjeables. No hay dinero real, depósitos, retiros ni
pasarela de pago.

**Stack:** FastAPI · SQLAlchemy 2.0 · PostgreSQL 16 · SvelteKit 5 · Tailwind 4 · Terraform

---

## Arrancar en local

Requisitos: Docker, Python 3.13 con [uv](https://docs.astral.sh/uv/), Node 22.

```bash
make up                      # PostgreSQL + migraciones
make seed                    # temporada de demo con datos
cd web && npm install && cd ..

make backend                 # API en :8000  (una terminal)
make web                     # app en :5173  (otra terminal)
```

Abre **http://localhost:5173**. `make help` lista todos los targets.

### Cuentas de demo

`make seed` deja tres jugadores listos, todos con contraseña **`quinielas2026`**:

| Cuenta | Estado inicial |
|---|---|
| `mariana@nexutest.mx` | 8 pts (marcador exacto), apuesta ganada, 1ª del ranking |
| `beto@nexutest.mx` | 0 pts pero **el balance más alto** — los dos ejes son independientes |
| `karla@nexutest.mx` | 3 pts (ganador acertado, marcador errado), apuesta perdida |

Para el panel de administración, promueve una cuenta:

```bash
make admin EMAIL=mariana@nexutest.mx
```

También puedes registrarte desde la app; cada cuenta nueva arranca con 1 000 créditos.

### Qué mirar

- **`/ranking`** — Beto está arriba en créditos y abajo en puntos. Es la regla R7: los puntos
  vienen del pronóstico, los créditos de la apuesta, y no se tocan.
- **`/partidos`** — abre una tarjeta: pronóstico de marcador, apuesta al resultado con la
  ganancia calculada en vivo, y la **línea de tiempo de franjas de gol** (no un desplegable).
  Hay partidos en los cuatro estados: abierto, por cerrar, cerrado y liquidado.
- **`/admin`** — mueve el slider de fuerza de un equipo y observa **el momio caer**. Es la
  mecánica central del producto hecha visible.

---

## Arquitectura

Tres capas y un núcleo puro:

```
app/api/       routers FastAPI, DTOs, códigos de estado
      │
app/services/  lógica transaccional: apostar, liquidar, cancelar, registrar
      │                    │
app/engine/          app/models/
  (PURO)              (SQLAlchemy)
```

`app/engine/` no importa `sqlalchemy`, `fastapi` ni nada con I/O, y nunca llama
`datetime.now()` — el instante entra por parámetro. No es una aspiración: sus tests corren
**con PostgreSQL apagado**.

| Regla de negocio | Vive en |
|---|---|
| R1 momios · R2 franjas · R8 puntuación | `app/engine/` — funciones puras |
| R3 cierre de apuestas | `engine/rules.py::is_open_for_betting(kickoff_at, now)` |
| R4 momio congelado | `bets.odds_snapshot` + `services/betting.py` |
| R5 ledger append-only | `services/wallet.py` — única puerta de escritura |
| R6 liquidación idempotente | `services/settlement.py` + bloqueo pesimista |
| R7 puntos ≠ créditos | dos rutas de código sin acoplamiento |
| R9 cancelación | `services/settlement.py::cancel_match` |

---

## Verificar

```bash
make test        # 58 tests
make check       # mypy --strict, ruff y svelte-check

# El gate que importa: el motor no toca la base.
docker compose stop db
cd backend && uv run pytest tests/engine/ -v    # pasa igual, en <2s
docker compose start db
```

Los invariantes arquitectónicos son grepeables y deben salir **vacíos**:

```bash
grep -rnE "sqlalchemy|fastapi|datetime\.now|from app\." backend/app/engine/   # A1, A2
grep -rn  "HTTPException" backend/app/services/ backend/app/engine/           # A4
grep -rnE "\* *odds|HOME_ADVANTAGE|DRAW_BASE" backend/app/services/           # A5
```

### El requisito central

Para todo par de fuerzas `(1..100, 1..100)` con `strength_home > strength_away` se cumple
`odds_home < odds_away`. Verificado sobre los 10 000 pares, sin excepciones:

```
rival_strength     local      empate     visita
  10               1.10       18.86      11.12
  50               1.74        5.13       3.53
  100              2.62        3.41       2.65
```

Existe margen de la casa en todo el dominio (`1/odds_home + 1/odds_draw + 1/odds_away > 1`),
con mínimo `1.004845` en el par extremo `(100, 1)`, donde el clamp `MIN_ODDS = 1.01` lo
erosiona sin eliminarlo.

---

## Desplegar

AWS + Cloudflare. Fargate con sidecar de `cloudflared`, así que **el security group no abre
ni un puerto**: el túnel sale hacia Cloudflare. RDS privada, frontend estático en S3 tras el
proxy de Cloudflare.

```bash
cp infra/terraform.tfvars.example infra/terraform.tfvars   # tu email para el budget
echo "<token>" > .cloudflare-token                         # Tunnel:Edit, DNS:Edit, Zone:Read

make infra     # terraform apply
make deploy    # imagen -> ECR -> ECS, y frontend -> S3
make logs      # sigue el arranque
make destroy   # lo tira todo, sin dejar nada cobrando
```

La RDS es privada, así que no se puede sembrar desde fuera de la VPC: el contenedor **se
autoabastece** al arrancar (`SEED_DEMO=1`) migrando, sembrando y creando el administrador.
Todo idempotente. La contraseña del admin se genera aleatoria:

```bash
aws secretsmanager get-secret-value --secret-id quinielas/admin-password \
  --query SecretString --output text
```

---

## Estado y limitaciones conocidas

Lo que **no** está, dicho explícitamente:

- **Sin recuperación de contraseña.** Fuera del alcance del MVP (no hay email), pero un
  usuario que la olvide no tiene salida por la interfaz.
- **Tests de concurrencia no escritos.** El `SELECT ... FOR UPDATE` que evita el sobregiro
  está implementado, pero no hay una prueba que lo demuestre bajo carga. Decisión consciente
  de alcance, anotada en el PRD (Phase 4 queda en 18/20).
- **Sin proveedor externo de resultados.** El administrador los captura a mano, incluido el
  minuto de cada gol.
- **Sin ligas privadas, notificaciones ni apuestas en vivo.**

---

## Documentación

| Documento | Qué contiene |
|---|---|
| [`docs/quinielas-futbol/prd.md`](docs/quinielas-futbol/prd.md) | PRD: reglas R1–R9, arquitectura A1–A5, plan por fases |
| [`docs/quinielas-futbol/design-prd.md`](docs/quinielas-futbol/design-prd.md) | PRD de diseño |
| [`docs/quinielas-futbol/design/`](docs/quinielas-futbol/design/) | Canvas, `tokens.md` y verificación del DoD de diseño |
| [`docs/specs/`](docs/specs/) | Especificación técnica de cada fase |

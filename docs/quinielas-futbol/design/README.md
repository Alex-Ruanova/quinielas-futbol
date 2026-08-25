# Diseño — Quinielas de Fútbol (Phase 1)

**Estado:** entregado y aprobado por Alex (gate humano cerrado el 2026-08-25).

## Canvas publicado

- **URL:** https://claude.ai/design/p/f10221dc-93aa-436c-a2df-a53684af2b39?file=Quinielas+-+Canvas+de+Dise%C3%B1o.dc.html
- **projectId:** `f10221dc-93aa-436c-a2df-a53684af2b39`
- **Copia local del canvas:** [`canvas.dc.html`](./canvas.dc.html) (109 KB)
- **Tokens:** [`tokens.md`](./tokens.md) — la fuente única para `tailwind.config.ts` y `app.css`

El canvas se lee en el editor de Claude Design; `support.js` del proyecto remoto es el
runtime generado de ese editor (React + bindings `{{ }}` sobre `<x-dc>`) y **no** es código
de la aplicación. Los `{{ ... }}` de los artboards son slots dinámicos que el frontend
rellena desde la API.

## Artboards

| # | Artboard | Lo consume |
|---|---|---|
| 1a | Tokens y componentes base | Phase 7 (Tasks 7.2, 7.6) |
| A | Tarjeta de partido — cuatro estados | Phase 8 |
| B | Panel de próximos partidos | Phase 8 |
| C | Apuesta por franja de gol | Phase 8 |
| D | Ranking, historial y perfil | Phase 8 |
| E | Panel de administración | Phase 9 |
| F | Estados vacíos y de error | Phase 8 |

## Verificación del DoD de `design-prd.md`

| DoD | Evidencia |
|---|---|
| Canvas publicado, URL registrada | ✅ arriba |
| Artboards A–F, móvil y escritorio | ✅ 7 artboards; 7 marcos de `390px` + variantes de escritorio |
| Tarjeta de partido con sus 4 estados | ✅ Abierta, Cerrada, Liquidada, Cancelada |
| `tokens.md` con valores concretos | ✅ hex, `rem`, `px`; sin prosa |
| Estados de apuesta distinguibles sin color | ✅ forma + icono (`◷ ✓ ✕ ⊘`) + etiqueta |
| Cifras tabulares en momios/importes/marcadores | ✅ 166 usos de `tabular-nums`; utilidad `.num` |
| Temas claro y oscuro con contraste AA | ✅ ambos declarados, ratios anotados por token |
| Selector de franja = línea de tiempo | ✅ línea de 90 min partida en seis; **cero** `<select>` en el canvas |
| Slider de `strength` con momio y relación inversa | ✅ artboard E, `input[type=range]` + momio en vivo |

## Refinamientos que el canvas impone al backend

Detectados al leer los artboards; **no** estaban explícitos en `prd.md`:

1. **Momios por franja, no un escalar.** El artboard C muestra seis momios distintos
   (`4.60 4.20 3.80 3.60 3.90 3.30`), mientras R2 define un default único de `4.50`.
   `season.scoring_config` tiene que guardar un **mapa por franja** con fallback al
   default del motor, y `PATCH /admin/seasons/{id}/scoring` (Task 5.2) debe aceptarlo.
2. **Etiquetas con guion largo.** El canvas muestra `0–15`, `76–90+` (en-dash); el enum
   `GoalBand` del backend usa guion corto (`0-15`). La traducción es de presentación:
   el frontend formatea, la API sigue enviando el valor del enum. No cambiar el enum.
3. **"Histórico de la liga"** (`la franja 76–90+ concentra el 24% de los goles`) es un
   dato que ninguna fase del backend produce. En el MVP se omite o se calcula en el
   cliente sobre los partidos ya liquidados; no se inventa un endpoint para él.

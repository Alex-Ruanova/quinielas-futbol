# Spec — Phase 7: Frontend — fundación, sistema de diseño y auth

## Goal
Base de SvelteKit, cliente API tipado y pantallas de cuenta. Es la fundación sobre la que
las Phases 8 y 9 construyen sus pantallas.

## Nota de agente (viene del PRD)
No hay especialista en Svelte en el registro, así que esta fase la lleva `typescript-pro`.
El agente **debe** consultar el MCP oficial de Svelte (`mcp__svelte__*`) antes de escribir
componentes y volver a validarlos con `svelte-autofixer` al terminar. No es opcional: es un
DoD de la fase.

## Entorno
- Node 22.17.0, npm 10.9.2. El frontend vive en `web/`.
- Backend disponible en `http://localhost:8000` con
  `uv run uvicorn app.main:app --reload` desde `backend/`.
- Los tokens de diseño están en `docs/quinielas-futbol/design/tokens.md` — **ya existen**,
  la Phase 1 está cerrada y aprobada. Los artboards están en
  `docs/quinielas-futbol/design/canvas.dc.html` (HTML plano, se puede leer y grepear).

## Implementation Steps
1. **SvelteKit + TypeScript + Tailwind** en `web/`. Svelte 5 (runas) y Tailwind 4 si el
   MCP de Svelte confirma que es el estado del arte; si no, la última estable que sí lo sea.
2. **Traducir `tokens.md` a `tailwind.config.ts` y `app.css`.** Uno a uno: cada hex, cada
   `rem`, cada radio y cada sombra del documento. **Cualquier color fuera de los tokens es
   un fallo de la fase.** Los dos temas se declaran como dos juegos de variables CSS bajo
   `:root` y `[data-theme="dark"]`, con el oscuro por defecto — el claro no es un
   post-proceso. Incluye la fuente Archivo (400–800) y la utilidad `.num` con
   `font-variant-numeric: tabular-nums`.
3. **Tipos desde el OpenAPI real.** Script de `package.json` con `openapi-typescript`
   apuntando al `openapi.json` del backend corriendo. **Prohibido escribir tipos de API a
   mano** — es un DoD verificable.
4. **`lib/api/client.ts`** — fetch tipado, inyección del JWT, y mapeo explícito de cada
   código de error del backend a un mensaje legible en español:
   - `401` → sesión expirada, redirige a login
   - `402` → saldo insuficiente
   - `409` → apuestas cerradas para ese partido / email ya registrado
   - `422` → datos inválidos (muestra el detalle del backend)
   Ningún fallo silencioso: toda respuesta no-2xx produce un error tipado.
5. **Sesión y guardas.** Store de sesión, guard de rutas, redirección a login en `401`.
   Pantallas de registro, login y perfil. Barra superior persistente con el balance.
6. **Componentes base** según el artboard 1a: `Button`, `Card`, `Money`, `OddsChip`,
   `StatusBadge`, `Countdown`, `TeamRow`.
   - `Money` usa cifras tabulares y signo.
   - `StatusBadge` implementa los cuatro estados con **color + forma + icono + etiqueta**:
     `pendiente` pill borde discontinuo `◷`, `ganada` rect 6px relleno sólido `✓`,
     `perdida` rect 2px borde sólido `✕`, `anulada` pill punteado tachado `⊘`.
     Distinguirlos solo por color es un fallo de accesibilidad explícito del design-prd.
   - `Countdown` pulsa (`pulseUrgent`, 1.6s) cuando faltan <15 min, y **respeta
     `prefers-reduced-motion`** con badge sólido sin animación.

## Edge Cases
- Objetivo táctil mínimo de 44px en móvil para chips, inputs y botones.
- Breakpoint único relevante: `768px` — de una columna a grid + panel lateral de 380px.
- El JWT se guarda de forma que sobreviva un refresh, y el balance de la barra se revalida
  tras cada operación que mueva el saldo.

## Testing Plan (ligero — decisión explícita de Alex)
Sin suite de tests de frontend. La verificación es:
1. `npm run build` y `npm run check` sin errores de tipo, con salida mostrada.
2. Los tipos del cliente se generaron desde el OpenAPI real (se ve el script y el archivo generado).
3. Flujo manual: registrarse → ver balance `1000` en la barra → cerrar sesión → login →
   el balance persiste.
4. Un `401` de la API redirige a login en vez de romper la pantalla.
5. Los componentes se validaron con el MCP de Svelte y no quedan advertencias abiertas.

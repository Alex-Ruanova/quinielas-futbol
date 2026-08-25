# Spec — Phase 8: Frontend — panel del usuario

## Goal
Las pantallas del jugador: próximos partidos, pronóstico de marcador, apuesta al resultado,
apuesta a la franja del gol, ranking, historial y saldo. Implementa los artboards A, B, C,
D y F del canvas.

## Fuente de verdad visual
`docs/quinielas-futbol/design/canvas.dc.html` (HTML plano, grepeable). Artboards:
- **A** — tarjeta de partido, cuatro estados: `abierto`, `por cerrar`, `cerrado`, `liquidado`
- **B** — panel de próximos partidos (móvil 390 con tarjeta expandida; escritorio 1280 con panel lateral)
- **C** — apuesta por franja de gol sobre línea de tiempo
- **D** — ranking, historial y perfil
- **F** — estados vacíos y de error

Los componentes base (`Button`, `Card`, `Money`, `OddsChip`, `StatusBadge`, `Countdown`,
`TeamRow`) y los tokens ya existen de la Phase 7. **Reutilízalos, no los redefinas.**

## Contradicción del canvas que NO debes replicar
El artboard B rotula el pronóstico como *"+5 pts exacto · +2 acertando ganador"*. **R8 del
PRD fija 3 puntos por acertar el ganador**, y el PRD dice que las reglas canónicas ganan
sobre cualquier fase que las contradiga. Además esos puntos son configurables por
temporada (`scoring_config`). Por tanto: **no hardcodees ni "+2" ni "+3"** — lee los
valores de la temporada desde la API y formatea el texto con ellos.

## Rutas
- `/partidos` — artboards A + B. Próximos partidos con equipos, hora **local** del usuario
  (el backend envía UTC), countdown al cierre, y los momios como chips seleccionables.
- `/partidos/[id]` o panel lateral en escritorio — la tarjeta expandida con los tres bloques:
  1. Pronóstico de marcador (precargado si ya existe)
  2. Apuesta al resultado
  3. Apuesta a la franja de gol
- `/ranking` — tabla de posiciones: `Pos · Usuario · Puntos · Exactos · Balance`. La fila
  del usuario actual va destacada ("tú").
- `/mis-apuestas` — historial: `Partido/mercado · Selección · Momio · Stake · Pago`, con
  `StatusBadge` en los cuatro estados.
- `/saldo` — movimientos del ledger: `Fecha · Concepto · Monto · Balance`.
- `/perfil` — nombre visible, teléfono, email de contacto.

## Detalles que el canvas fija y hay que respetar
- **Formato numérico `es-MX` con espacio de millares**: `1 240 cr`, no `1,240`. El canvas
  lo hace explícito (`.replace(/,/g, ' ')`).
- **Ganancia potencial en vivo**: `stake * odds`, recalculada al cambiar monto o selección,
  **antes** de confirmar. Al liquidar, el pago mostrado tiene que coincidir exactamente con
  el del backend.
- **Los dos ejes separados y visibles**: cabecera con `Puntos ... pts · ranking #N` y
  `Créditos ... cr virtuales`, con la leyenda de que los puntos vienen de pronósticos y los
  créditos de apuestas. No los unifiques en una sola métrica.
- **"Pronosticar no consume créditos"** tiene que estar dicho en la UI (R7).
- **Franja de gol (artboard C)**: línea de tiempo de 90 minutos partida en seis, **nunca un
  dropdown**. Marcas de medio tiempo. Selección de equipo opcional (`Cualquiera` / local /
  visitante). El texto "el tiempo añadido cuenta dentro de 76–90+" va visible.
- **Etiquetas con guion largo** en presentación (`0–15`, `76–90+`), pero el valor enviado a
  la API es el del enum con guion corto (`0-15`, `76-90+`). Traduce en la capa de vista.
- **Estados de partido**: `cerrado` y `liquidado` se muestran en solo lectura, con ambos
  formularios deshabilitados. El de `por cerrar` lleva el aviso de últimos minutos y el
  countdown pulsando.
- **Chips**: seleccionado usa `accent #C8FF4D` con tinta `#0B0F0D`; en reposo `surface-1`
  con borde `#2F3A33`.

## Estados vacíos y de error (artboard F) — los cinco
Cada uno dice **qué pasó + qué puede hacer el usuario**, con acción:
1. Sin partidos próximos → "Ver la jornada anterior"
2. **Saldo insuficiente** (`402`) → "Te faltan N cr", con botón que baja el monto al máximo posible
3. **Apuesta rechazada por cierre** (`409`) → "El partido cerró mientras confirmabas. No se
   descontó ningún crédito", con enlace a otros partidos abiertos
4. Temporada sin liquidar → la tabla es parcial
5. Sin apuestas todavía → aclarando que los pronósticos viven en los puntos, no aquí

Un stack trace nunca llega a la pantalla.

## Testing Plan (ligero — decisión explícita de Alex)
Sin suite automatizada. Verificación:
1. `npm run check` y `npm run build` en verde, salida mostrada.
2. Flujo manual con screenshots contra el backend real: pronosticar → apostar al resultado →
   apostar a la franja → el balance baja por el stake.
3. La ganancia potencial mostrada coincide con `stake * odds` de la respuesta del backend.
4. En un partido con `kickoff_at` pasado, ambos formularios aparecen deshabilitados.
5. Apostar por encima del balance muestra el estado de error del artboard F, no un stack trace.
6. Tras liquidar, `/mis-apuestas` refleja `WON`/`LOST` con el pago correcto y `/ranking`
   muestra los puntos.
7. Componentes validados con el MCP de Svelte, sin advertencias abiertas.

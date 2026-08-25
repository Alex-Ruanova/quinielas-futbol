# Spec — Phase 9: Frontend — panel de administración

## Goal
La interfaz mínima pero completa para operar el sistema sin tocar la base ni `curl`.
Implementa el artboard E. Corre en paralelo con la Phase 8 porque no comparte archivos:
todo vive bajo `web/src/routes/admin/`.

## Fuente de verdad visual
`docs/quinielas-futbol/design/canvas.dc.html`, artboard **E · Panel de administración**.
Los componentes base y los tokens ya existen de la Phase 7. Reutilízalos.

## Pantallas

### 1. Equipos — el slider que hace visible la mecánica del producto
Formulario de equipo: `Nombre`, `Abreviatura`, `Fuerza (strength)` como slider `1..100` con
las marcas `1 · débil`, `50 · promedio`, `100 · potencia`.

Debajo, en vivo contra `GET /api/v1/admin/teams/{id}/odds-preview?opponent_strength=50`:
- `{equipo} gana {odds_home}`
- `Rival gana {odds_away}`
- `Probabilidad implícita`
- Una barra que **encoge** al subir la fuerza

**Este es el DoD central de la fase:** al mover el slider hacia arriba, el momio tiene que
**bajar** visiblemente. Es la mecánica del producto hecha evidente para el admin. Debouncea
la llamada, pero no la elimines: los momios los calcula el backend (A5), el frontend
**no** replica la fórmula de R1.

### 2. Capturador de resultado
Marcador `{local} N – M {visitante}` más una lista editable de goles:
`Equipo · Minuto · T. añadido (checkbox) · eliminar`, con un `+ Agregar gol`.

- Validación **en cliente**: el número de goles y su reparto por equipo tienen que cuadrar
  con el marcador. Indicador `✓ N goles cuadran` / error si no. El botón de liquidar queda
  deshabilitado mientras no cuadre.
- Muestra las **franjas que estos goles liquidan** (`0–15`, `46–60`, `76–90+`), derivadas
  de los minutos capturados. Es la retroalimentación que evita capturar mal.
- El backend rechaza igualmente si se fuerza — la validación de cliente es conveniencia, no
  la defensa.

### 3. Temporadas, jornadas y partidos
- Lista de temporadas (`Apertura 2026`, `Clausura 2026`) con `+ Nueva temporada`.
- Tabla de jornadas: `Jornada · Partidos · Cierre · Estado`, con los estados
  `◷ Abierta` / `✓ Liquidada`. `+ Agregar jornada`.
- Alta de partidos dentro de una jornada, respetando la ventana de la jornada (el backend
  devuelve `422` si el `kickoff_at` cae fuera; muéstralo legible).
- Editor de `scoring_config`: los puntos por acierto **y el mapa de momios por franja**
  (seis franjas, con el default del motor cuando una falta). Ver el refinamiento en
  `docs/quinielas-futbol/design/README.md`.

### 4. Operaciones destructivas
`Cancelar partido` y `Reintentar liquidación`, **ambas con confirmación explícita** que diga
qué va a pasar: cancelar deja todas las apuestas en `VOID` y reembolsa los stakes.

## Guardas
- Toda la sección bajo `require_admin` en el backend. En el frontend, un usuario no-admin
  que navega a `/admin` es rechazado y redirigido, no ve la interfaz a medias.
- Las etiquetas de franja se muestran con guion largo pero se envían con el guion corto del
  enum.

## Testing Plan (ligero — decisión explícita de Alex)
Sin suite automatizada. Verificación:
1. `npm run check` en verde, salida mostrada.
2. Flujo manual con screenshots: crear temporada → jornada → equipos con strengths dispares
   → partido → capturar resultado con minutos de gol → ver las apuestas liquidadas.
3. **El slider de `strength` muestra el momio y se ve caer al subir la fuerza** (screenshot
   de dos posiciones del slider).
4. El editor de resultado impide enviar si los goles no cuadran con el marcador.
5. Un usuario no-admin que navega a `/admin` es rechazado.

# PRD de Diseño — Quinielas de Fútbol

> Documento **independiente**, pensado para trabajarse en paralelo con la implementación del backend. Corresponde a la Phase 1 de [`prd.md`](./prd.md) y no depende de que exista una sola línea de código.
>
> **Entregable:** un canvas de Claude Design publicado como Artifact, más `design/tokens.md`.
> **Se ejecuta con:** la skill `design` desde la sesión principal.

## 1. Contexto del producto

Aplicación de quinielas de fútbol con dos audiencias:

- **El jugador.** Ve los partidos que se aproximan, pronostica el marcador para acumular **puntos** en un ranking, y apuesta **créditos virtuales** en dos mercados: el resultado (1X2) y la **franja de 15 minutos en la que caerá un gol**. Cada apuesta muestra un momio: apostarle al equipo grande paga poco, al chico paga mucho.
- **El administrador.** Da de alta temporadas, jornadas, equipos y partidos, y captura los resultados incluyendo **el minuto de cada gol**.

El saldo es crédito virtual no canjeable. No hay dinero real, ni depósitos, ni retiros. **El diseño no debe evocar una casa de apuestas real** ni usar lenguaje de dinero real ("depositar", "retirar", "cajero"): es un juego de puntos y créditos entre aficionados.

## 2. Qué hace difícil este diseño

Estas son las tensiones reales; un canvas que no las resuelva no sirve, por bonito que sea.

1. **Densidad numérica.** Cada tarjeta de partido lleva tres momios, un marcador, una hora, una cuenta regresiva y posiblemente una apuesta previa. Todo eso tiene que leerse de un vistazo en un teléfono.
2. **Dos mercados en la misma tarjeta.** Resultado y franja de gol son apuestas distintas sobre el mismo partido. Deben coexistir sin que el usuario se confunda sobre a qué le está apostando.
3. **Puntos y créditos son ejes independientes.** Un usuario puede pronosticar sin apostar. La interfaz tiene que dejar clarísimo que son dos cosas separadas y no una sola barra de progreso.
4. **El tiempo manda.** Un partido se cierra a la hora del saque inicial. La transición de "puedes apostar" a "ya no" tiene que ser evidente antes de que ocurra, no una sorpresa.
5. **Cifras que no bailan.** Momios y saldos se comparan en columna. Sin cifras tabulares, la tabla de posiciones y el historial se ven rotos.

## 3. Sistema de diseño

### 3.1 Tokens (entregable: `design/tokens.md`)

- **Paleta:** superficies, texto, acento primario, y **semánticas de estado de apuesta**: `pendiente`, `ganada`, `perdida`, `anulada`. Estas cuatro **no pueden distinguirse solo por color** — cada una necesita también forma, icono o etiqueta, porque el 8% de los hombres tiene daltonismo y esta app es de aficionados al fútbol.
- **Tipografía:** escala completa, y una variante con **cifras tabulares** (`font-variant-numeric: tabular-nums`) obligatoria para momios, importes, marcadores y minutos.
- **Espaciado, radios y elevación:** escalas explícitas, no valores sueltos.
- **Temas claro y oscuro:** ambos definidos desde el principio. El tema oscuro no es un post-proceso.
- Valores concretos: hex, `rem`, `px`. Nada de "azul deportivo" o "espaciado generoso".

### 3.2 Componentes base

`Button`, `Card`, `Money` (importe con cifras tabulares y signo), `OddsChip` (momio seleccionable), `StatusBadge` (los cuatro estados de apuesta), `Countdown`, `TeamRow` (escudo + nombre).

## 4. Artboards requeridos

Cada uno en móvil (390px) y escritorio (1280px) donde el layout cambie de verdad.

### A. Tarjeta de partido *(el componente central — el resto se construye sobre él)*
Escudos y nombres de ambos equipos, hora local, cuenta regresiva al cierre, y los tres momios como chips seleccionables. Estados a diseñar: **abierto**, **por cerrar** (últimos minutos, visualmente urgente), **cerrado** (solo lectura), **liquidado** (con el resultado y si el usuario ganó o perdió).

### B. Panel de próximos partidos
La pantalla de inicio del jugador. Lista de tarjetas agrupadas por jornada. Incluye, expandido dentro de la tarjeta o en un panel lateral:
- **Formulario de pronóstico de marcador** — dos campos numéricos, precargado si ya pronosticó.
- **Formulario de apuesta al resultado** — selección, monto, y un bloque de **ganancia potencial** que se actualiza mientras el usuario teclea el monto. Este bloque es el que convence de apostar: dale peso visual.

### C. Apuesta por franja de gol
Selector de las seis franjas (`0-15`, `16-30`, `31-45`, `46-60`, `61-75`, `76-90+`) **sobre una línea de tiempo horizontal del partido**, no como un dropdown. El usuario debe *ver* el partido de 90 minutos partido en seis. Incluye selector de equipo opcional ("cualquier equipo" por defecto), monto y ganancia potencial.

### D. Ranking y perfil
- Tabla de posiciones de la temporada: posición, usuario, puntos, y como columnas secundarias marcadores exactos y balance de créditos. Destacar la fila del usuario actual.
- Historial de apuestas: partido, mercado, selección, **momio congelado**, stake, estado y pago.
- Movimientos del saldo: fecha, concepto, monto, balance resultante.
- Perfil: nombre visible, teléfono y email de contacto.

### E. Panel de administración
- Alta y edición de equipos con el **`strength` como slider de 1 a 100** que muestra en vivo el momio resultante contra un rival de referencia. Este control es la mecánica del producto hecha visible: al subir la fuerza, el momio debe verse **caer**.
- Alta de temporadas, jornadas y partidos.
- **Capturador de resultado**: marcador más una lista editable de goles (equipo, minuto, casilla de tiempo añadido), con la validación de que los goles cuadran con el marcador.

### F. Estados vacíos y de error
Sin partidos próximos · saldo insuficiente para apostar · apuesta rechazada porque el partido ya cerró · temporada sin liquidar todavía · sin apuestas en el historial. Cada uno con un texto que diga qué pasó y qué puede hacer el usuario.

## 5. Definition of Done

- [ ] El canvas está publicado como Artifact y su URL queda registrada en `docs/quinielas-futbol/design/README.md`.
- [ ] Existen artboards para los seis grupos A–F, en móvil y escritorio donde el layout cambia.
- [ ] La tarjeta de partido tiene sus cuatro estados diseñados, no solo el abierto.
- [ ] `docs/quinielas-futbol/design/tokens.md` tiene valores concretos (hex, `rem`, `px`) listos para traducirse a `tailwind.config.ts`, no descripciones en prosa.
- [ ] Los cuatro estados de apuesta se distinguen por forma, icono o etiqueta **además** del color.
- [ ] Todo momio, importe, marcador y minuto usa cifras tabulares en la especificación tipográfica.
- [ ] Los temas claro y oscuro están definidos ambos, con contraste verificado (mínimo AA) en texto sobre superficie.
- [ ] El selector de franja de gol es una línea de tiempo, no un dropdown.
- [ ] El slider de `strength` del panel admin muestra el momio resultante y su relación inversa.
- [ ] **Gate humano:** Alex revisó y aprobó el canvas.

## 6. Cómo lo consume el frontend

| Entregable | Lo consume |
|---|---|
| `design/tokens.md` | Phase 7, Task 7.2 → `tailwind.config.ts` y `app.css` |
| Componentes base (§3.2) | Phase 7, Task 7.6 |
| Artboards A, B, C, D, F | Phase 8 — panel del usuario |
| Artboard E | Phase 9 — panel de administración |

La Phase 7 puede arrancar sin el canvas (andamiaje, cliente API, auth) y esperar solo para las tareas de estilo. Las Phases 8 y 9 **no arrancan** hasta que el canvas esté aprobado: reimplementar pantallas cuesta más que iterar artboards.

## 7. Fuera de alcance del diseño

Ligas privadas entre amigos · notificaciones · apuestas en vivo · cualquier pantalla de depósito, retiro o método de pago · deportes distintos del fútbol.

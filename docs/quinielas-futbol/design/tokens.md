# Tokens — Quinielas de Fútbol

Listos para traducir a `tailwind.config.ts` / `app.css`. Base tipográfica 16px = 1rem.

## 1. Color

### 1.1 Tema oscuro (default)

| Token | Hex | Uso |
|---|---|---|
| `surface-0` | `#0B0F0D` | fondo de app |
| `surface-1` | `#121815` | campos, chips en reposo |
| `surface-2` | `#18201C` | tarjetas |
| `surface-3` | `#1E2620` | botones secundarios, filas hover |
| `border` | `#263029` | bordes 1px |
| `border-strong` | `#3A473F` | bordes de input, foco en reposo |
| `text` | `#F2F5F2` | texto primario (contraste 15.4:1 sobre `surface-2`) |
| `text-muted` | `#9AA79E` | texto secundario (6.1:1 sobre `surface-2`) |
| `text-faint` | `#5F6B62` | metadatos (3.2:1 — solo ≥14px bold o no esencial) |
| `accent` | `#C8FF4D` | acento primario (fills, momio seleccionado) |
| `accent-hover` | `#E4FF9B` | hover de fill |
| `accent-ink` | `#0B0F0D` | texto sobre `accent` (14.8:1) |
| `accent-ink-soft` | `#3B5209` | etiqueta secundaria sobre `accent` (5.9:1) |

### 1.2 Tema claro

| Token | Hex | Uso |
|---|---|---|
| `surface-0` | `#F4F6F1` | fondo de app |
| `surface-1` | `#FFFFFF` | tarjetas |
| `surface-2` | `#E7EBE2` | campos, chips |
| `border` | `#DDE3D8` | bordes 1px |
| `text` | `#11170F` | texto primario (16.9:1 sobre blanco) |
| `text-muted` | `#556053` | texto secundario (6.6:1) |
| `accent` | `#C8FF4D` | fills (siempre con `accent-ink`) |
| `accent-text` | `#2D6A1E` | acento en texto y links (5.2:1 sobre blanco) |

El tema oscuro no es un post-proceso: ambos temas se declaran como dos juegos de
variables CSS bajo `:root` y `[data-theme="dark"]`.

### 1.3 Semánticas de estado de apuesta

Cada estado se distingue por **color + forma + icono + etiqueta** (nunca solo color).

| Estado | Color oscuro | Color claro | Forma | Icono | Etiqueta |
|---|---|---|---|---|---|
| `pendiente` | `#E9B949` texto/borde, fondo transparente | `#8A6410` | pill `999px`, borde **discontinuo** 1px | `◷` | "Pendiente" |
| `ganada` | `#35D07F` fondo, `#08170E` texto | `#137A47` fondo, `#FFFFFF` texto | rect `6px`, **relleno sólido** | `✓` | "Ganada" |
| `perdida` | `#F2545B` borde, `#FF8A8F` texto | `#B7202A` | rect `2px`, borde **sólido 2px** | `✕` | "Perdida" |
| `anulada` | `#7E8A81` borde punteado, `#9AA79E` texto | `#6B7469` | pill `999px`, borde **punteado**, texto tachado | `⊘` | "Anulada" |

Auxiliares: `positive` `#35D07F` / `#137A47`, `negative` `#F2545B` / `#B7202A`,
`urgent` `#E9B949` (superficie de urgencia `#1E1B14` oscuro, `#FFF7E2` claro).

## 2. Tipografía

Familia única: **Archivo** (400, 500, 600, 700, 800). Fallback `system-ui, sans-serif`.

| Token | Tamaño | Peso | Line-height | Tracking |
|---|---|---|---|---|
| `display` | `2.5rem` (40px) | 800 | 1.05 | `-0.03em` |
| `h1` | `2.125rem` (34px) | 800 | 1.1 | `-0.02em` |
| `h2` | `1.5rem` (24px) | 800 | 1.15 | `-0.02em` |
| `h3` | `1.25rem` (20px) | 800 | 1.2 | `-0.01em` |
| `body-lg` | `1.0625rem` (17px) | 600 | 1.4 | 0 |
| `body` | `1rem` (16px) | 500 | 1.5 | 0 |
| `body-sm` | `0.875rem` (14px) | 500 | 1.55 | 0 |
| `caption` | `0.75rem` (12px) | 600 | 1.4 | 0 |
| `label` | `0.6875rem` (11px) | 800 | 1.2 | `0.1em`, uppercase |

### Cifras tabulares — obligatorias

`font-variant-numeric: tabular-nums` en **momios, importes, marcadores, minutos, puntos,
contadores y toda columna numérica de tabla**. Utilidad `.num`:

```css
.num { font-variant-numeric: tabular-nums; font-feature-settings: "tnum" 1; }
```

Escala numérica destacada: `num-xl` `2.5rem`/800 (ganancia potencial),
`num-lg` `1.375rem`/800 (momio en chip), `num-md` `1.0625rem`/800 (momio en lista),
`num-sm` `0.8125rem`/700 (tablas).

## 3. Espaciado

`space-1` 4px · `space-2` 8px · `space-3` 12px · `space-4` 16px · `space-5` 20px ·
`space-6` 24px · `space-8` 32px · `space-12` 48px · `space-16` 64px.

Padding de tarjeta móvil `14–16px`; escritorio `18–24px`. Gap entre chips de momio `8px`;
entre tarjetas `14px` móvil / `20px` escritorio.

## 4. Radios

`radius-xs` 2px (badge "perdida") · `radius-sm` 4px · `radius-md` 6px (badge "ganada") ·
`radius-lg` 10px (botón, input) · `radius-xl` 12px (chip de momio) ·
`radius-2xl` 16px (tarjeta) · `radius-3xl` 28px (marco de pantalla móvil) ·
`radius-full` 999px (pill).

## 5. Elevación

| Token | Valor |
|---|---|
| `elev-0` | `none` — default en oscuro; la jerarquía la da la superficie |
| `elev-1` | `0 1px 2px rgba(11,15,13,.4)` |
| `elev-2` | `0 8px 24px rgba(11,15,13,.45)` |
| `elev-urgent` | `0 0 0 1px rgba(233,185,73,.25), 0 12px 32px rgba(233,185,73,.08)` |
| `elev-1` (claro) | `0 1px 2px rgba(17,23,15,.06)` |
| `elev-2` (claro) | `0 8px 24px rgba(17,23,15,.06)` |

## 6. Otros

- **Objetivo táctil mínimo:** 44px de alto en móvil (chips, inputs, botones).
- **Foco:** `outline: 2px solid #C8FF4D; outline-offset: 2px` (oscuro) / `#2D6A1E` (claro).
- **Urgencia:** animación `pulseUrgent` 1.6s ease-in-out infinite en el countdown cuando
  faltan <15 min; respeta `prefers-reduced-motion` (sin pulso, badge sólido).
- **Breakpoint único relevante:** `768px` — de una columna de tarjetas a grid + panel
  lateral de 380px.

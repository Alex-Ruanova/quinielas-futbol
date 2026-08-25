import type { Config } from 'tailwindcss';

/**
 * Traducción 1:1 de docs/quinielas-futbol/design/tokens.md.
 * Los colores apuntan a variables CSS declaradas en src/app.css (:root /
 * [data-theme="dark"] / [data-theme="light"]) — nunca un hex fijo aquí, así ambos
 * temas comparten una sola fuente de verdad.
 */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	theme: {
		extend: {
			fontFamily: {
				sans: ['Archivo', 'system-ui', 'sans-serif']
			},
			colors: {
				surface: {
					0: 'var(--color-surface-0)',
					1: 'var(--color-surface-1)',
					2: 'var(--color-surface-2)',
					3: 'var(--color-surface-3)'
				},
				border: 'var(--color-border)',
				'border-strong': 'var(--color-border-strong)',
				text: {
					DEFAULT: 'var(--color-text)',
					muted: 'var(--color-text-muted)',
					faint: 'var(--color-text-faint)'
				},
				accent: {
					DEFAULT: 'var(--color-accent)',
					hover: 'var(--color-accent-hover)',
					ink: 'var(--color-accent-ink)',
					'ink-soft': 'var(--color-accent-ink-soft)',
					text: 'var(--color-accent-text)'
				},
				status: {
					pending: 'var(--color-status-pending)',
					'won-bg': 'var(--color-status-won-bg)',
					'won-text': 'var(--color-status-won-text)',
					lost: 'var(--color-status-lost)',
					'lost-text': 'var(--color-status-lost-text)',
					void: 'var(--color-status-void)',
					'void-text': 'var(--color-status-void-text)'
				},
				positive: 'var(--color-positive)',
				negative: 'var(--color-negative)',
				urgent: {
					DEFAULT: 'var(--color-urgent)',
					surface: 'var(--color-urgent-surface)'
				},
				focus: 'var(--color-focus)'
			},
			spacing: {
				'space-1': '0.25rem',
				'space-2': '0.5rem',
				'space-3': '0.75rem',
				'space-4': '1rem',
				'space-5': '1.25rem',
				'space-6': '1.5rem',
				'space-8': '2rem',
				'space-12': '3rem',
				'space-16': '4rem'
			},
			borderRadius: {
				xs: '2px',
				sm: '4px',
				md: '6px',
				lg: '10px',
				xl: '12px',
				'2xl': '16px',
				'3xl': '28px',
				full: '999px'
			},
			boxShadow: {
				'elev-0': 'none',
				'elev-1': 'var(--shadow-elev-1)',
				'elev-2': 'var(--shadow-elev-2)',
				'elev-urgent': 'var(--shadow-elev-urgent)'
			},
			fontSize: {
				display: ['2.5rem', { lineHeight: '1.05', letterSpacing: '-0.03em', fontWeight: '800' }],
				h1: ['2.125rem', { lineHeight: '1.1', letterSpacing: '-0.02em', fontWeight: '800' }],
				h2: ['1.5rem', { lineHeight: '1.15', letterSpacing: '-0.02em', fontWeight: '800' }],
				h3: ['1.25rem', { lineHeight: '1.2', letterSpacing: '-0.01em', fontWeight: '800' }],
				'body-lg': ['1.0625rem', { lineHeight: '1.4', letterSpacing: '0em', fontWeight: '600' }],
				body: ['1rem', { lineHeight: '1.5', letterSpacing: '0em', fontWeight: '500' }],
				'body-sm': ['0.875rem', { lineHeight: '1.55', letterSpacing: '0em', fontWeight: '500' }],
				caption: ['0.75rem', { lineHeight: '1.4', letterSpacing: '0em', fontWeight: '600' }],
				label: ['0.6875rem', { lineHeight: '1.2', letterSpacing: '0.1em', fontWeight: '800' }],
				'num-xl': ['2.5rem', { fontWeight: '800' }],
				'num-lg': ['1.375rem', { fontWeight: '800' }],
				'num-md': ['1.0625rem', { fontWeight: '800' }],
				'num-sm': ['0.8125rem', { fontWeight: '700' }]
			},
			screens: {
				md: '768px'
			},
			animation: {
				'pulse-urgent': 'pulseUrgent 1.6s ease-in-out infinite'
			}
		}
	}
} satisfies Config;

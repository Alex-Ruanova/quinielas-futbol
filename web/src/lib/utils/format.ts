const numberFormatter = (fractionDigits: 0 | 2) =>
	new Intl.NumberFormat('es-MX', { minimumFractionDigits: fractionDigits, maximumFractionDigits: 2 });

/** `es-MX` con separador de millares en espacio, ej. `1 240` — nunca coma. */
export function formatAmount(value: number): string {
	const hasFraction = !Number.isInteger(value);
	return numberFormatter(hasFraction ? 2 : 0)
		.formatToParts(Math.abs(value))
		.map((part) => (part.type === 'group' ? ' ' : part.value))
		.join('');
}

/** Créditos con signo. `signed` antepone `+` a valores positivos (para deltas). */
export function formatMoney(value: number | string, signed = false): string {
	const numeric = typeof value === 'string' ? Number(value) : value;
	const sign = numeric < 0 ? '−' : signed && numeric > 0 ? '+' : '';
	return `${sign}${formatAmount(numeric)} cr`;
}

const dateTimeFormatter = new Intl.DateTimeFormat('es-MX', {
	weekday: 'short',
	hour: '2-digit',
	minute: '2-digit'
});

const dayFormatter = new Intl.DateTimeFormat('es-MX', { day: '2-digit', month: 'short' });

/** El backend siempre manda UTC; aquí se traduce a la hora local del navegador. */
export function formatKickoff(iso: string): string {
	return dateTimeFormatter.format(new Date(iso));
}

export function formatShortDate(iso: string): string {
	return dayFormatter.format(new Date(iso));
}

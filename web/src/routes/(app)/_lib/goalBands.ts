import type { GoalBand } from '../_api/matches';

/** Línea de 90 minutos partida en seis franjas fijas; el valor enviado a la API usa
 * guion corto, la etiqueta en pantalla usa guion largo (en-dash). */
export const GOAL_BANDS: { value: GoalBand; label: string; short: string }[] = [
	{ value: '0-15', label: '0–15', short: '0–15' },
	{ value: '16-30', label: '16–30', short: '16–30' },
	{ value: '31-45', label: '31–45', short: '31–45' },
	{ value: '46-60', label: '46–60', short: '46–60' },
	{ value: '61-75', label: '61–75', short: '61–75' },
	{ value: '76-90+', label: '76–90+', short: '76–90' }
];

export function goalBandLabel(band: GoalBand): string {
	return GOAL_BANDS.find((entry) => entry.value === band)?.label ?? band;
}

import type { GoalBand } from './api';

/** Etiquetas en guion largo para pantalla; el valor enviado a la API usa el guion corto del enum. */
export const GOAL_BANDS: { value: GoalBand; label: string; min: number; max: number }[] = [
	{ value: '0-15', label: '0–15', min: 0, max: 15 },
	{ value: '16-30', label: '16–30', min: 16, max: 30 },
	{ value: '31-45', label: '31–45', min: 31, max: 45 },
	{ value: '46-60', label: '46–60', min: 46, max: 60 },
	{ value: '61-75', label: '61–75', min: 61, max: 75 },
	{ value: '76-90+', label: '76–90+', min: 76, max: Infinity }
];

export function bandForMinute(minute: number): GoalBand {
	const found = GOAL_BANDS.find((band) => minute >= band.min && minute <= band.max);
	return (found ?? GOAL_BANDS[GOAL_BANDS.length - 1]).value;
}

export function bandLabel(band: GoalBand): string {
	return GOAL_BANDS.find((b) => b.value === band)?.label ?? band;
}

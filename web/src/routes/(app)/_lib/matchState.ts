import type { MatchUpcoming } from '../_api/matches';

export type MatchUiState = 'abierto' | 'por-cerrar' | 'cerrado' | 'liquidado';

export const URGENT_THRESHOLD_MS = 15 * 60 * 1000;

/** Deriva el estado visual de la tarjeta a partir del status del backend y el kickoff,
 * nunca al revés: el backend no expone un estado "en juego" explícito. */
export function deriveMatchState(
	match: Pick<MatchUpcoming, 'kickoff_at'> & { status?: string },
	now = Date.now()
): MatchUiState {
	if (match.status && match.status !== 'SCHEDULED') return 'liquidado';
	const remainingMs = new Date(match.kickoff_at).getTime() - now;
	if (remainingMs <= 0) return 'cerrado';
	if (remainingMs <= URGENT_THRESHOLD_MS) return 'por-cerrar';
	return 'abierto';
}

export function isBettable(state: MatchUiState): boolean {
	return state === 'abierto' || state === 'por-cerrar';
}

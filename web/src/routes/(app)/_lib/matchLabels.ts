import type { MatchUpcoming } from '../_api/matches';

type MatchLabel = {
	homeTeamId: string;
	awayTeamId: string;
	homeTeamName: string;
	awayTeamName: string;
};

/**
 * `/bets` solo trae `match_id`; no hay un endpoint no-admin que resuelva nombres de
 * equipo para partidos ya liquidados (desaparecen de `/matches/upcoming`). Este caché
 * en memoria guarda lo que sí vimos en `/matches/upcoming` durante la sesión, para que
 * `/mis-apuestas` no repita llamadas; si el partido nunca pasó por ahí, se muestra un
 * folio corto en su lugar — hueco de API documentado, no una API inventada.
 */
const cache = new Map<string, MatchLabel>();

export function rememberMatches(matches: MatchUpcoming[]): void {
	for (const match of matches) {
		cache.set(match.id, {
			homeTeamId: match.home_team_id,
			awayTeamId: match.away_team_id,
			homeTeamName: match.home_team_name,
			awayTeamName: match.away_team_name
		});
	}
}

export function matchLabel(matchId: string): string {
	const entry = cache.get(matchId);
	if (!entry) return `Partido ${matchId.slice(0, 8)}`;
	return `${entry.homeTeamName} – ${entry.awayTeamName}`;
}

export function teamLabel(matchId: string, teamId: string | null | undefined): string | null {
	if (!teamId) return null;
	const entry = cache.get(matchId);
	if (!entry) return null;
	if (entry.homeTeamId === teamId) return entry.homeTeamName;
	if (entry.awayTeamId === teamId) return entry.awayTeamName;
	return null;
}

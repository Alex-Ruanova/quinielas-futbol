import { apiCall, client } from '$lib/api/client';
import type { components } from '$lib/api/schema';

export type Team = components['schemas']['TeamRead'];
export type TeamCreate = components['schemas']['TeamCreate'];
export type TeamUpdate = components['schemas']['TeamUpdate'];
export type OddsPreview = components['schemas']['OddsPreview'];

export type Season = components['schemas']['SeasonRead'];
export type SeasonCreate = components['schemas']['SeasonCreate'];
export type ScoringConfigUpdate = components['schemas']['ScoringConfigUpdate'];

export type Round = components['schemas']['RoundRead'];
export type RoundCreate = components['schemas']['RoundCreate'];

export type Match = components['schemas']['MatchRead'];
export type MatchCreate = components['schemas']['MatchCreate'];
export type MatchStatus = components['schemas']['MatchStatus'];

export type ResultIn = components['schemas']['ResultIn'];
export type GoalIn = components['schemas']['GoalIn'];
export type GoalBand = components['schemas']['GoalBand'];
export type MatchResult = components['schemas']['MatchResultRead'];

export function listTeams(): Promise<Team[]> {
	return apiCall(client.GET('/api/v1/admin/teams', {}));
}

export function createTeam(body: TeamCreate): Promise<Team> {
	return apiCall(client.POST('/api/v1/admin/teams', { body }));
}

export function updateTeam(teamId: string, body: TeamUpdate): Promise<Team> {
	return apiCall(
		client.PATCH('/api/v1/admin/teams/{team_id}', { params: { path: { team_id: teamId } }, body })
	);
}

/** Momio real calculado por el motor del backend contra `opponent_strength`; nunca replicado en cliente.
 * `strength` simula una fuerza sin guardarla, para que el slider previsualice sin escribir en la base. */
export function oddsPreview(
	teamId: string,
	opponentStrength: number,
	strength?: number
): Promise<OddsPreview> {
	return apiCall(
		client.GET('/api/v1/admin/teams/{team_id}/odds-preview', {
			params: {
				path: { team_id: teamId },
				query: { opponent_strength: opponentStrength, strength }
			}
		})
	);
}

export function listSeasons(): Promise<Season[]> {
	return apiCall(client.GET('/api/v1/admin/seasons', {}));
}

export function createSeason(body: SeasonCreate): Promise<Season> {
	return apiCall(client.POST('/api/v1/admin/seasons', { body }));
}

export function updateScoring(seasonId: string, body: ScoringConfigUpdate): Promise<Season> {
	return apiCall(
		client.PATCH('/api/v1/admin/seasons/{season_id}/scoring', {
			params: { path: { season_id: seasonId } },
			body
		})
	);
}

export function listRounds(seasonId?: string): Promise<Round[]> {
	return apiCall(
		client.GET('/api/v1/admin/rounds', { params: { query: { season_id: seasonId ?? null } } })
	);
}

export function createRound(body: RoundCreate): Promise<Round> {
	return apiCall(client.POST('/api/v1/admin/rounds', { body }));
}

export function listMatches(roundId?: string): Promise<Match[]> {
	return apiCall(
		client.GET('/api/v1/admin/matches', { params: { query: { round_id: roundId ?? null } } })
	);
}

export function createMatch(body: MatchCreate): Promise<Match> {
	return apiCall(client.POST('/api/v1/admin/matches', { body }));
}

export function recordResult(matchId: string, body: ResultIn): Promise<MatchResult> {
	return apiCall(
		client.PUT('/api/v1/admin/matches/{match_id}/result', {
			params: { path: { match_id: matchId } },
			body
		})
	);
}

export function settleMatch(matchId: string): Promise<void> {
	return apiCall(
		client.POST('/api/v1/admin/matches/{match_id}/settle', { params: { path: { match_id: matchId } } })
	);
}

export function cancelMatch(matchId: string): Promise<void> {
	return apiCall(
		client.POST('/api/v1/admin/matches/{match_id}/cancel', { params: { path: { match_id: matchId } } })
	);
}

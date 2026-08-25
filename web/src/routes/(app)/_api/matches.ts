import { apiCall, client } from '$lib/api/client';
import type { components } from '$lib/api/schema';

export type MatchUpcoming = components['schemas']['MatchUpcomingRead'];
export type PredictionInput = components['schemas']['PredictionIn'];
export type PredictionRead = components['schemas']['PredictionRead'];
export type BetInput = components['schemas']['BetCreate'];
export type BetRead = components['schemas']['BetRead'];
export type GoalBand = components['schemas']['GoalBand'];

export async function getUpcomingMatches(): Promise<MatchUpcoming[]> {
	return apiCall(client.GET('/api/v1/matches/upcoming', {}));
}

export async function savePrediction(
	matchId: string,
	payload: PredictionInput
): Promise<PredictionRead> {
	return apiCall(
		client.PUT('/api/v1/matches/{match_id}/prediction', {
			params: { path: { match_id: matchId } },
			body: payload
		})
	);
}

export async function placeBet(matchId: string, payload: BetInput): Promise<BetRead> {
	return apiCall(
		client.POST('/api/v1/matches/{match_id}/bets', {
			params: { path: { match_id: matchId } },
			body: payload
		})
	);
}

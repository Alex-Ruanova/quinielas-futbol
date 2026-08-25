import { apiCall, client } from '$lib/api/client';
import type { components } from '$lib/api/schema';

export type LeaderboardEntry = components['schemas']['LeaderboardEntryRead'];
export type Season = components['schemas']['SeasonSummaryRead'];

export async function findActiveSeason(): Promise<Season | null> {
	try {
		const seasons = await apiCall(client.GET('/api/v1/seasons', {}));
		return seasons.find((season) => season.status === 'active') ?? seasons[0] ?? null;
	} catch {
		return null;
	}
}

export async function findActiveSeasonId(): Promise<string | null> {
	const season = await findActiveSeason();
	return season?.id ?? null;
}

export async function getLeaderboard(seasonId: string): Promise<LeaderboardEntry[]> {
	return apiCall(
		client.GET('/api/v1/seasons/{season_id}/leaderboard', {
			params: { path: { season_id: seasonId } }
		})
	);
}

import { apiCall, client } from '$lib/api/client';
import type { BetRead } from './matches';

export async function listMyBets(): Promise<BetRead[]> {
	return apiCall(client.GET('/api/v1/bets', {}));
}

import { apiCall, client } from '$lib/api/client';
import type { components } from '$lib/api/schema';

/* `/bets` devuelve la apuesta con el contexto del partido; `/matches/upcoming`
 * devuelve la version sin el, asi que no comparten tipo. */
export type BetWithMatch = components['schemas']['BetWithMatchRead'];

export async function listMyBets(): Promise<BetWithMatch[]> {
	return apiCall(client.GET('/api/v1/bets', {}));
}

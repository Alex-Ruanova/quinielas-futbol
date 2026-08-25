import { apiCall, client } from './client';
import { session } from '$lib/stores/session.svelte';

/** Revalida el balance de la barra superior; se llama tras cada operación que mueve saldo. */
export async function refreshBalance(): Promise<void> {
	const wallet = await apiCall(client.GET('/api/v1/wallet', {}));
	session.setBalance(wallet.balance);
}

import { apiCall, client } from '$lib/api/client';
import type { components } from '$lib/api/schema';

export type CreditTransaction = components['schemas']['CreditTransactionOut'];
export type CreditTransactionPage = components['schemas']['CreditTransactionPage'];

export async function listTransactions(page = 1, pageSize = 20): Promise<CreditTransactionPage> {
	return apiCall(
		client.GET('/api/v1/wallet/transactions', {
			params: { query: { page, page_size: pageSize } }
		})
	);
}

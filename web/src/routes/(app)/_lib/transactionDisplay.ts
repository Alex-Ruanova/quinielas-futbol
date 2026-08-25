import type { CreditTransaction } from '../_api/wallet';

const KIND_LABEL: Record<CreditTransaction['kind'], string> = {
	SEED: 'Créditos de bienvenida',
	STAKE: 'Apuesta',
	PAYOUT: 'Premio',
	REFUND: 'Reembolso'
};

export function conceptFor(tx: CreditTransaction, betLabel: (betId: string) => string | null): string {
	if (!tx.bet_id) return KIND_LABEL[tx.kind];
	return `${KIND_LABEL[tx.kind]} ${betLabel(tx.bet_id) ?? tx.bet_id.slice(0, 8)}`;
}

/** El endpoint no trae balance corriente por movimiento; se reconstruye hacia atrás desde
 * el balance actual asumiendo orden más-reciente-primero (así los devuelve el backend). */
export function withRunningBalance(
	transactions: CreditTransaction[],
	currentBalance: number
): { tx: CreditTransaction; balanceAfter: number }[] {
	let balance = currentBalance;
	const rows: { tx: CreditTransaction; balanceAfter: number }[] = [];
	for (const tx of transactions) {
		rows.push({ tx, balanceAfter: balance });
		balance -= Number(tx.amount);
	}
	return rows;
}

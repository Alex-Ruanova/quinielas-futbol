<script lang="ts">
	import { ApiError } from '$lib/api/client';
	import Button from '$lib/components/Button.svelte';
	import Money from '$lib/components/Money.svelte';
	import { session } from '$lib/stores/session.svelte';
	import { listMyBets } from '../_api/bets';
	import { listTransactions, type CreditTransaction } from '../_api/wallet';
	import { matchLabel } from '../_lib/matchLabels';
	import { conceptFor, withRunningBalance } from '../_lib/transactionDisplay';
	import { formatShortDate } from '../_lib/localTime';
	import EmptyState from '../_components/EmptyState.svelte';

	let transactions = $state<CreditTransaction[]>([]);
	let betIdToMatchId = $state<Map<string, string>>(new Map());
	let loading = $state(true);
	let loadError = $state<ApiError | null>(null);

	async function load() {
		loading = true;
		loadError = null;
		try {
			const [page, bets] = await Promise.all([listTransactions(), listMyBets()]);
			transactions = page.items;
			betIdToMatchId = new Map(bets.map((bet) => [bet.id, bet.match_id]));
		} catch (error) {
			loadError = error instanceof ApiError ? error : new ApiError(0, 'No se pudo cargar tu saldo.');
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		load();
	});

	function betLabel(betId: string): string | null {
		const matchId = betIdToMatchId.get(betId);
		return matchId ? matchLabel(matchId) : null;
	}

	const rows = $derived(withRunningBalance(transactions, Number(session.balance ?? 0)));
</script>

<svelte:head>
	<title>Mi saldo — Quinielas</title>
</svelte:head>

<div class="flex flex-col gap-5">
	<div class="flex items-center justify-between">
		<h1 class="text-h2 text-text">Mi saldo</h1>
		<Money value={session.balance ?? 0} class="text-num-lg" />
	</div>

	{#if loading}
		<p class="text-body-sm text-text-muted">Cargando movimientos…</p>
	{:else if loadError}
		<EmptyState icon="⊘" tone="negative" title="No pudimos cargar tu saldo" description={loadError.message}>
			<Button variant="secondary" onclick={load}>Reintentar</Button>
		</EmptyState>
	{:else if rows.length === 0}
		<EmptyState
			icon="▢"
			title="Sin movimientos todavía"
			description="Tus créditos de bienvenida y el resultado de tus apuestas aparecerán aquí."
		/>
	{:else}
		<div class="overflow-hidden rounded-2xl border border-border bg-surface-2">
			<div
				class="grid grid-cols-[70px_1fr_80px_90px] gap-3 border-b border-border px-4 py-2.5 text-caption font-extrabold uppercase tracking-wide text-text-muted"
			>
				<span>Fecha</span><span>Concepto</span><span class="text-right">Monto</span><span class="text-right">Balance</span>
			</div>
			{#each rows as row (row.tx.id)}
				<div
					class="grid grid-cols-[70px_1fr_80px_90px] items-center gap-3 border-b border-border/60 px-4 py-2.5 text-body-sm last:border-b-0"
				>
					<span class="num text-text-muted">{formatShortDate(row.tx.created_at)}</span>
					<span class="text-text">{conceptFor(row.tx, betLabel)}</span>
					<Money value={Number(row.tx.amount)} signed class="text-num-sm justify-self-end" />
					<span class="num justify-self-end font-bold text-text">{Number(row.balanceAfter).toFixed(0)}</span>
				</div>
			{/each}
		</div>
	{/if}
</div>

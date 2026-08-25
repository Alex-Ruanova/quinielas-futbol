<script lang="ts">
	import { ApiError } from '$lib/api/client';
	import Button from '$lib/components/Button.svelte';
	import Money from '$lib/components/Money.svelte';
	import StatusBadge from '$lib/components/StatusBadge.svelte';
	import { listMyBets, type BetWithMatch } from '../_api/bets';
	import { describeSelection, marketLabel, payoutFor } from '../_lib/betDisplay';
	import { matchLabel } from '../_lib/matchLabels';
	import EmptyState from '../_components/EmptyState.svelte';

	let bets = $state<BetWithMatch[]>([]);
	let loading = $state(true);
	let loadError = $state<ApiError | null>(null);

	async function load() {
		loading = true;
		loadError = null;
		try {
			bets = await listMyBets();
		} catch (error) {
			loadError = error instanceof ApiError ? error : new ApiError(0, 'No se pudo cargar tu historial.');
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		load();
	});
</script>

<svelte:head>
	<title>Mis apuestas — Quinielas</title>
</svelte:head>

<div class="flex flex-col gap-5">
	<h1 class="text-h2 text-text">Mis apuestas</h1>

	{#if loading}
		<p class="text-body-sm text-text-muted">Cargando historial…</p>
	{:else if loadError}
		<EmptyState icon="⊘" tone="negative" title="No pudimos cargar tu historial" description={loadError.message}>
			<Button variant="secondary" onclick={load}>Reintentar</Button>
		</EmptyState>
	{:else if bets.length === 0}
		<EmptyState
			icon="▢"
			title="Todavía no has apostado"
			description="Tu historial se llena en cuanto confirmes tu primera apuesta. Pronosticar marcadores no aparece aquí: eso vive en tus puntos."
		>
			<a href="/partidos"><Button variant="primary">Ir a los próximos partidos</Button></a>
		</EmptyState>
	{:else}
		<div class="overflow-hidden rounded-2xl border border-border bg-surface-2">
			<div
				class="grid grid-cols-[1fr_repeat(3,minmax(0,80px))] gap-3 border-b border-border px-4 py-2.5 text-caption font-extrabold uppercase tracking-wide text-text-muted md:grid-cols-[1fr_100px_80px_90px_100px]"
			>
				<span>Partido / mercado</span>
				<span class="hidden text-right md:block">Selección</span>
				<span class="text-right">Momio</span>
				<span class="text-right">Stake</span>
				<span class="text-right">Pago</span>
			</div>
			{#each bets as bet (bet.id)}
				{@const payout = payoutFor(bet)}
				<div
					class="grid grid-cols-[1fr_repeat(3,minmax(0,80px))] items-center gap-3 border-b border-border/60 px-4 py-3 text-body-sm last:border-b-0 md:grid-cols-[1fr_100px_80px_90px_100px]"
				>
					<div class="flex flex-col">
						<span class="font-semibold text-text">{matchLabel(bet.match_id, bet.match)}</span>
						<span class="text-caption text-text-faint">{marketLabel(bet)}</span>
					</div>
					<span class="hidden text-right text-text-muted md:block">{describeSelection(bet)}</span>
					<span class="num text-right text-text">{Number(bet.odds_snapshot).toFixed(2)}</span>
					<span class="num text-right text-text">{Number(bet.stake).toFixed(0)}</span>
					<span class="text-right">
						{#if payout.display === 'pending'}
							<span class="num font-extrabold text-status-pending">◷ —</span>
						{:else if payout.display === 'void'}
							<span class="num font-extrabold text-text-muted">⊘ {payout.amount}</span>
						{:else}
							<Money value={payout.amount} signed class="text-num-sm" />
						{/if}
					</span>
				</div>
			{/each}
			<div class="flex flex-wrap gap-2 border-t border-border p-4">
				<StatusBadge status="pendiente" />
				<StatusBadge status="ganada" />
				<StatusBadge status="perdida" />
				<StatusBadge status="anulada" />
			</div>
		</div>
	{/if}
</div>

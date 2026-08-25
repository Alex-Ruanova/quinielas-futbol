<script lang="ts">
	import { ApiError } from '$lib/api/client';
	import { refreshBalance } from '$lib/api/wallet';
	import Button from '$lib/components/Button.svelte';
	import OddsChip from '$lib/components/OddsChip.svelte';
	import { session } from '$lib/stores/session.svelte';
	import { formatAmount } from '$lib/utils/format';
	import { placeBet, type BetRead } from '../_api/matches';
	import BetErrorPanel from './BetErrorPanel.svelte';

	let {
		matchId,
		homeLabel,
		awayLabel,
		oddsHome,
		oddsDraw,
		oddsAway,
		disabled = false,
		onplaced
	}: {
		matchId: string;
		homeLabel: string;
		awayLabel: string;
		oddsHome: number;
		oddsDraw: number;
		oddsAway: number;
		disabled?: boolean;
		onplaced?: (bet: BetRead) => void;
	} = $props();

	type Pick = 'HOME' | 'DRAW' | 'AWAY';

	let pick = $state<Pick>('HOME');
	let stakeInput = $state('100');
	let placing = $state(false);
	let apiError = $state<ApiError | null>(null);
	let placedJustNow = $state(false);

	const balance = $derived(Number(session.balance ?? 0));
	const stake = $derived(Number(stakeInput) || 0);
	const odds = $derived({ HOME: oddsHome, DRAW: oddsDraw, AWAY: oddsAway }[pick]);
	const payout = $derived(Math.round(stake * odds));
	const netGain = $derived(payout - stake);
	const chipState = (target: Pick) => (disabled ? 'bloqueado' : pick === target ? 'seleccionado' : 'reposo');

	function digitsOnly(value: string): string {
		return value.replace(/[^0-9]/g, '').slice(0, 6);
	}

	async function confirm() {
		apiError = null;
		placedJustNow = false;
		if (stake <= 0) {
			return;
		}
		if (stake > balance) {
			apiError = new ApiError(402, 'Saldo insuficiente para esta operación.');
			return;
		}
		placing = true;
		try {
			const bet = await placeBet(matchId, {
				selection: { market: 'OUTCOME', pick },
				stake
			});
			placedJustNow = true;
			await refreshBalance();
			onplaced?.(bet);
		} catch (error) {
			apiError = error instanceof ApiError ? error : new ApiError(0, 'No se pudo registrar la apuesta.');
		} finally {
			placing = false;
		}
	}
</script>

<div class="flex flex-col gap-2.5 rounded-xl border border-accent/30 bg-surface-1 p-3.5">
	<div class="flex items-center justify-between">
		<span class="text-label uppercase text-text-muted">2 · Apuesta al resultado</span>
		<span class="num text-caption font-bold text-text-muted">saldo {formatAmount(balance)} cr</span>
	</div>

	<div class="flex gap-2">
		<OddsChip label={homeLabel} odds={oddsHome} state={chipState('HOME')} onclick={() => (pick = 'HOME')} disabled={disabled} />
		<OddsChip label="EMPATE" odds={oddsDraw} state={chipState('DRAW')} onclick={() => (pick = 'DRAW')} disabled={disabled} />
		<OddsChip label={awayLabel} odds={oddsAway} state={chipState('AWAY')} onclick={() => (pick = 'AWAY')} disabled={disabled} />
	</div>

	<div class="flex items-center gap-2">
		<input
			bind:value={stakeInput}
			oninput={() => (stakeInput = digitsOnly(stakeInput))}
			inputmode="numeric"
			aria-label="Monto a apostar"
			{disabled}
			class="num min-h-11 min-w-0 flex-1 rounded-lg border border-border-strong bg-surface-0 px-3 py-2.5 text-body-lg font-bold text-text"
		/>
		<Button variant="secondary" {disabled} onclick={() => (stakeInput = '50')}>50</Button>
		<Button variant="secondary" {disabled} onclick={() => (stakeInput = '100')}>100</Button>
		<Button variant="secondary" {disabled} onclick={() => (stakeInput = String(Math.trunc(balance)))}>Todo</Button>
	</div>

	<div class="flex items-end justify-between gap-3 rounded-xl bg-accent p-4">
		<div class="flex flex-col gap-0.5">
			<span class="text-label uppercase text-accent-ink-soft">Ganancia potencial</span>
			<span class="num text-num-xl leading-none text-accent-ink">{formatAmount(payout)} cr</span>
		</div>
		<span class="num text-caption font-bold text-accent-ink-soft">
			{stake} cr × {odds.toFixed(2)} → +{formatAmount(Math.max(0, netGain))} neto
		</span>
	</div>

	<Button variant="primary" disabled={disabled || placing || stake <= 0} onclick={confirm}>
		{placing ? 'Confirmando…' : `Apostar ${formatAmount(stake)} cr`}
	</Button>

	<p class="text-caption leading-relaxed text-text-faint">
		Créditos virtuales, no canjeables. El momio se congela al confirmar.
	</p>

	{#if apiError}
		<BetErrorPanel
			error={apiError}
			{balance}
			{stake}
			onLowerStake={(max) => {
				stakeInput = String(Math.trunc(max));
				apiError = null;
			}}
			ondismiss={() => (apiError = null)}
		/>
	{/if}
	{#if placedJustNow}
		<p class="text-body-sm font-semibold text-positive" role="status">
			Apuesta confirmada · momio {odds.toFixed(2)} congelado.
		</p>
	{/if}
</div>

<script lang="ts">
	import { ApiError } from '$lib/api/client';
	import { refreshBalance } from '$lib/api/wallet';
	import Button from '$lib/components/Button.svelte';
	import { session } from '$lib/stores/session.svelte';
	import { formatAmount } from '$lib/utils/format';
	import { placeBet, type BetRead, type GoalBand } from '../_api/matches';
	import { GOAL_BANDS } from '../_lib/goalBands';
	import BetErrorPanel from './BetErrorPanel.svelte';

	let {
		matchId,
		homeTeamId,
		homeLabel,
		awayTeamId,
		awayLabel,
		goalBandOdds,
		disabled = false,
		onplaced
	}: {
		matchId: string;
		homeTeamId: string;
		homeLabel: string;
		awayTeamId: string;
		awayLabel: string;
		goalBandOdds: Record<string, string>;
		disabled?: boolean;
		onplaced?: (bet: BetRead) => void;
	} = $props();

	type TeamFilter = 'any' | 'home' | 'away';

	let band = $state<GoalBand>('0-15');
	let team = $state<TeamFilter>('any');
	let stakeInput = $state('30');
	let placing = $state(false);
	let apiError = $state<ApiError | null>(null);
	let placedJustNow = $state(false);

	const balance = $derived(Number(session.balance ?? 0));
	const stake = $derived(Number(stakeInput) || 0);
	const odds = $derived(Number(goalBandOdds[band] ?? 0));
	const payout = $derived(Math.round(stake * odds));

	function digitsOnly(value: string): string {
		return value.replace(/[^0-9]/g, '').slice(0, 6);
	}

	function teamIdFor(filter: TeamFilter): string | null {
		if (filter === 'home') return homeTeamId;
		if (filter === 'away') return awayTeamId;
		return null;
	}

	async function confirm() {
		apiError = null;
		placedJustNow = false;
		if (stake <= 0) return;
		if (stake > balance) {
			apiError = new ApiError(402, 'Saldo insuficiente para esta operación.');
			return;
		}
		placing = true;
		try {
			const bet = await placeBet(matchId, {
				selection: { market: 'GOAL_BAND', band, team_id: teamIdFor(team) },
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

<div class="flex flex-col gap-4 rounded-xl border border-border bg-surface-1 p-3.5">
	<div class="flex items-center justify-between">
		<span class="text-label uppercase text-text-muted">3 · Apuesta a la franja de gol</span>
		<span class="num text-caption font-bold text-text-muted">saldo {formatAmount(balance)} cr</span>
	</div>

	<div class="flex flex-col gap-2">
		<div class="flex justify-between text-caption font-bold text-text-faint">
			<span>0'</span><span>45'</span><span>90+'</span>
		</div>
		<div class="flex h-20 gap-0.5" role="radiogroup" aria-label="Franja de gol">
			{#each GOAL_BANDS as option, index (option.value)}
				<button
					type="button"
					role="radio"
					aria-checked={band === option.value}
					{disabled}
					onclick={() => (band = option.value)}
					class="num flex flex-1 flex-col justify-between px-1.5 py-2 text-left disabled:cursor-not-allowed disabled:opacity-45"
					class:bg-accent={band === option.value}
					class:text-accent-ink={band === option.value}
					class:bg-surface-0={band !== option.value}
					class:text-text={band !== option.value}
					class:border={true}
					class:border-accent={band === option.value}
					class:border-border-strong={band !== option.value}
					style="border-radius: {index === 0
						? '10px 3px 3px 10px'
						: index === GOAL_BANDS.length - 1
							? '3px 10px 10px 3px'
							: '3px'}"
				>
					<span class="text-caption font-extrabold">{option.label}</span>
					<span class="text-body-sm font-extrabold">
						{Number(goalBandOdds[option.value] ?? 0).toFixed(2)}
					</span>
				</button>
			{/each}
		</div>
		<div class="flex items-center gap-2 pl-0.5">
			<span class="h-2 w-2 rounded-full bg-text-faint"></span>
			<span class="h-px flex-1 bg-border"></span>
			<span class="text-caption font-bold uppercase text-text-faint">medio tiempo</span>
			<span class="h-px flex-1 bg-border"></span>
			<span class="h-2 w-2 rounded-full bg-text-faint"></span>
		</div>
		<p class="text-caption leading-relaxed text-text-faint">
			El tiempo añadido cuenta dentro de <span class="num font-bold text-text-muted">76–90+</span>.
		</p>
	</div>

	<div class="flex flex-col gap-2">
		<span class="text-label uppercase text-text-muted">¿Quién anota? (opcional)</span>
		<div class="flex gap-2">
			{#each [
				['any', 'Cualquiera'],
				['home', homeLabel],
				['away', awayLabel]
			] as [value, label] (value)}
				<button
					type="button"
					{disabled}
					onclick={() => (team = value as TeamFilter)}
					class="min-h-11 flex-1 rounded-full border border-border-strong px-2 py-2.5 text-center text-body-sm font-bold disabled:cursor-not-allowed disabled:opacity-45"
					class:bg-accent={team === value}
					class:text-accent-ink={team === value}
					class:bg-surface-0={team !== value}
					class:text-text={team !== value}
				>
					{label}
				</button>
			{/each}
		</div>
	</div>

	<div class="flex items-center justify-between text-caption font-bold text-text-muted">
		<span class="uppercase">Monto</span>
		<span class="num">saldo {formatAmount(balance)} cr</span>
	</div>
	<input
		bind:value={stakeInput}
		oninput={() => (stakeInput = digitsOnly(stakeInput))}
		inputmode="numeric"
		aria-label="Monto a apostar a la franja"
		{disabled}
		class="num min-h-11 rounded-lg border border-border-strong bg-surface-0 px-3 py-2.5 text-body-lg font-bold text-text"
	/>

	<div class="flex flex-col gap-0.5 rounded-xl bg-accent p-4">
		<span class="text-label uppercase text-accent-ink-soft">Ganancia potencial</span>
		<span class="num text-num-xl leading-none text-accent-ink">{formatAmount(payout)} cr</span>
		<span class="num text-caption font-bold text-accent-ink-soft">
			{stake} cr × {odds.toFixed(2)} · franja {GOAL_BANDS.find((b) => b.value === band)?.label}
		</span>
	</div>

	<Button variant="primary" disabled={disabled || placing || stake <= 0} onclick={confirm}>
		{placing ? 'Confirmando…' : `Apostar a ${GOAL_BANDS.find((b) => b.value === band)?.label}`}
	</Button>

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
			Apuesta a franja confirmada · momio {odds.toFixed(2)} congelado.
		</p>
	{/if}
</div>

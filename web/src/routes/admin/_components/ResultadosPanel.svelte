<script lang="ts">
	import { onMount } from 'svelte';
	import Card from '$lib/components/Card.svelte';
	import Button from '$lib/components/Button.svelte';
	import StatusBadge from '$lib/components/StatusBadge.svelte';
	import { ApiError } from '$lib/api/client';
	import {
		cancelMatch,
		listMatches,
		listRounds,
		listTeams,
		recordResult,
		settleMatch
	} from '../_lib/api';
	import type { GoalIn, Match, Round, Team } from '../_lib/api';
	import { GOAL_BANDS, bandForMinute, bandLabel } from '../_lib/bands';
	import GoalEditor from './GoalEditor.svelte';
	import ConfirmDialog from './ConfirmDialog.svelte';

	let teams = $state<Team[]>([]);
	let rounds = $state<Round[]>([]);
	let matches = $state<Match[]>([]);
	let loadError = $state('');

	let selectedRoundId = $state<string | null>(null);
	let selectedMatchId = $state<string | null>(null);

	let homeScore = $state(0);
	let awayScore = $state(0);
	let goals = $state<GoalIn[]>([]);

	let liquidating = $state(false);
	let actionError = $state('');
	let actionOk = $state('');

	let confirmSettleOpen = $state(false);
	let confirmCancelOpen = $state(false);

	const teamsById = $derived(new Map(teams.map((team) => [team.id, team])));
	const selectedMatch = $derived(matches.find((match) => match.id === selectedMatchId) ?? null);
	const homeTeam = $derived(
		selectedMatch ? teamsById.get(selectedMatch.home_team_id) ?? null : null
	);
	const awayTeam = $derived(
		selectedMatch ? teamsById.get(selectedMatch.away_team_id) ?? null : null
	);

	const homeGoalsCount = $derived(
		selectedMatch ? goals.filter((g) => g.team_id === selectedMatch.home_team_id).length : 0
	);
	const awayGoalsCount = $derived(
		selectedMatch ? goals.filter((g) => g.team_id === selectedMatch.away_team_id).length : 0
	);
	const scoreMatchesGoals = $derived(
		goals.length === homeScore + awayScore &&
			homeGoalsCount === homeScore &&
			awayGoalsCount === awayScore
	);
	const settledBands = $derived.by(() => {
		const present = new Set(goals.map((g) => bandForMinute(g.minute)));
		return GOAL_BANDS.filter((band) => present.has(band.value));
	});

	async function loadCatalog() {
		try {
			[teams, rounds] = await Promise.all([listTeams(), listRounds()]);
			if (rounds.length > 0) await selectRound(rounds[0].id);
		} catch (error) {
			loadError = error instanceof ApiError ? error.message : 'No se pudo cargar el catálogo.';
		}
	}

	onMount(loadCatalog);

	async function selectRound(roundId: string) {
		selectedRoundId = roundId;
		selectedMatchId = null;
		actionError = '';
		actionOk = '';
		try {
			matches = await listMatches(roundId);
		} catch (error) {
			loadError = error instanceof ApiError ? error.message : 'No se pudieron cargar los partidos.';
		}
	}

	function selectMatch(match: Match) {
		selectedMatchId = match.id;
		homeScore = match.home_score ?? 0;
		awayScore = match.away_score ?? 0;
		goals = [];
		actionError = '';
		actionOk = '';
	}

	async function onLiquidar(event: SubmitEvent) {
		event.preventDefault();
		if (!selectedMatchId || !scoreMatchesGoals) return;
		liquidating = true;
		actionError = '';
		actionOk = '';
		try {
			await recordResult(selectedMatchId, { home_score: homeScore, away_score: awayScore, goals });
			actionOk = 'Resultado capturado y apuestas liquidadas.';
			matches = await listMatches(selectedRoundId ?? undefined);
		} catch (error) {
			actionError = error instanceof ApiError ? error.message : 'No se pudo liquidar el partido.';
		} finally {
			liquidating = false;
		}
	}

	async function onRetrySettle() {
		if (!selectedMatchId) return;
		actionError = '';
		actionOk = '';
		try {
			await settleMatch(selectedMatchId);
			actionOk = 'Se reintentó la liquidación.';
		} catch (error) {
			actionError = error instanceof ApiError ? error.message : 'No se pudo reintentar la liquidación.';
		}
	}

	async function onCancel() {
		if (!selectedMatchId) return;
		actionError = '';
		actionOk = '';
		try {
			await cancelMatch(selectedMatchId);
			actionOk = 'Partido cancelado: apuestas anuladas y stakes reembolsados.';
			matches = await listMatches(selectedRoundId ?? undefined);
		} catch (error) {
			actionError = error instanceof ApiError ? error.message : 'No se pudo cancelar el partido.';
		}
	}
</script>

<div class="flex flex-col gap-5">
	<Card>
		<h2 class="text-h3 text-text">Capturador de resultado</h2>
		{#if loadError}
			<p class="mt-3 text-body-sm font-semibold text-negative">{loadError}</p>
		{/if}

		<div class="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
			<label class="flex flex-col gap-1.5">
				<span class="text-label uppercase text-text-muted">Jornada</span>
				<select
					value={selectedRoundId}
					onchange={(event) => selectRound((event.target as HTMLSelectElement).value)}
					class="min-h-11 rounded-lg border border-border-strong bg-surface-1 px-3 py-2 text-body text-text"
				>
					{#each rounds as round (round.id)}
						<option value={round.id}>{round.name}</option>
					{/each}
				</select>
			</label>
			<label class="flex flex-col gap-1.5">
				<span class="text-label uppercase text-text-muted">Partido</span>
				<select
					value={selectedMatchId}
					onchange={(event) => {
						const match = matches.find((m) => m.id === (event.target as HTMLSelectElement).value);
						if (match) selectMatch(match);
					}}
					class="min-h-11 rounded-lg border border-border-strong bg-surface-1 px-3 py-2 text-body text-text"
				>
					<option value={null} disabled>Elige un partido</option>
					{#each matches as match (match.id)}
						<option value={match.id}>
							{teamsById.get(match.home_team_id)?.name ?? '?'} – {teamsById.get(match.away_team_id)
								?.name ?? '?'} ({match.status})
						</option>
					{/each}
				</select>
			</label>
		</div>

		{#if selectedMatch && homeTeam && awayTeam}
			<form class="mt-5 flex flex-col gap-4" onsubmit={onLiquidar}>
				<div class="flex flex-wrap items-center gap-4">
					<div class="flex items-center gap-2">
						<span class="text-body-lg font-semibold text-text">{homeTeam.name}</span>
						<input
							type="number"
							min="0"
							bind:value={homeScore}
							class="num min-h-11 w-16 rounded-lg border border-border-strong bg-surface-1 text-center text-h3 text-text"
						/>
					</div>
					<span class="text-h3 text-text-faint">–</span>
					<div class="flex items-center gap-2">
						<input
							type="number"
							min="0"
							bind:value={awayScore}
							class="num min-h-11 w-16 rounded-lg border border-border-strong bg-surface-1 text-center text-h3 text-text"
						/>
						<span class="text-body-lg font-semibold text-text">{awayTeam.name}</span>
					</div>

					<span
						class="ml-auto inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-caption font-bold {scoreMatchesGoals
							? 'bg-status-won-bg text-status-won-text'
							: 'border border-negative text-negative'}"
					>
						{scoreMatchesGoals
							? `✓ ${goals.length} goles cuadran`
							: `✕ ${goals.length} goles no cuadran con ${homeScore}–${awayScore}`}
					</span>
				</div>

				<GoalEditor bind:goals homeTeam={{ id: homeTeam.id, name: homeTeam.name }} awayTeam={{ id: awayTeam.id, name: awayTeam.name }} />

				<div class="rounded-lg border border-border bg-surface-1 p-3 text-body-sm text-text-muted">
					Franjas liquidadas por estos goles:
					{#if settledBands.length === 0}
						<span class="text-text-faint">ninguna todavía.</span>
					{:else}
						{#each settledBands as band, index (band.value)}
							<span class="num font-bold text-accent">{band.label}</span
							>{index < settledBands.length - 1 ? ', ' : '.'}
						{/each}
					{/if}
				</div>

				{#if actionError}
					<p class="text-body-sm font-semibold text-negative" role="alert">{actionError}</p>
				{/if}
				{#if actionOk}
					<p class="text-body-sm font-semibold text-positive">{actionOk}</p>
				{/if}

				<Button type="submit" variant="primary" disabled={!scoreMatchesGoals || liquidating}>
					{liquidating ? 'Liquidando…' : 'Liquidar partido'}
				</Button>
			</form>

			<div class="mt-6 flex flex-wrap items-center gap-3 border-t border-border pt-4">
				<StatusBadge
					status={selectedMatch.status === 'FINISHED'
						? 'ganada'
						: selectedMatch.status === 'CANCELLED'
							? 'anulada'
							: 'pendiente'}
				/>
				<Button variant="secondary" onclick={() => (confirmSettleOpen = true)}>
					Reintentar liquidación
				</Button>
				<Button variant="secondary" onclick={() => (confirmCancelOpen = true)}>
					Cancelar partido
				</Button>
			</div>
		{/if}
	</Card>
</div>

<ConfirmDialog
	bind:open={confirmSettleOpen}
	title="Reintentar liquidación"
	description="Vuelve a procesar las apuestas pendientes de este partido contra el resultado ya capturado. Es idempotente: si ya se liquidó, no duplica pagos ni puntos."
	confirmLabel="Reintentar"
	onconfirm={onRetrySettle}
/>

<ConfirmDialog
	bind:open={confirmCancelOpen}
	title="Cancelar partido"
	description="Todas las apuestas de este partido quedarán en VOID y se reembolsa el stake completo a cada apostador. No se otorgan puntos."
	confirmLabel="Cancelar partido"
	onconfirm={onCancel}
/>

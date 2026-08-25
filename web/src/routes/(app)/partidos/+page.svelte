<script lang="ts">
	import { ApiError } from '$lib/api/client';
	import { session } from '$lib/stores/session.svelte';
	import Button from '$lib/components/Button.svelte';
	import { getUpcomingMatches, type MatchUpcoming, type BetRead, type PredictionRead } from '../_api/matches';
	import { findActiveSeasonId, getLeaderboard } from '../_api/leaderboard';
	import { rememberMatches } from '../_lib/matchLabels';
	import { deriveMatchState, isBettable } from '../_lib/matchState';
	import MatchCard from '../_components/MatchCard.svelte';
	import PredictionBlock from '../_components/PredictionBlock.svelte';
	import OutcomeBetBlock from '../_components/OutcomeBetBlock.svelte';
	import GoalBandBlock from '../_components/GoalBandBlock.svelte';
	import PointsCreditsHeader from '../_components/PointsCreditsHeader.svelte';
	import EmptyState from '../_components/EmptyState.svelte';

	let matches = $state<MatchUpcoming[]>([]);
	let loading = $state(true);
	let loadError = $state<ApiError | null>(null);
	let expandedId = $state<string | null>(null);
	let points = $state<number | null>(null);
	let rank = $state<number | null>(null);

	async function loadMatches() {
		loading = true;
		loadError = null;
		try {
			matches = await getUpcomingMatches();
			rememberMatches(matches);
		} catch (error) {
			loadError = error instanceof ApiError ? error : new ApiError(0, 'No se pudieron cargar los partidos.');
		} finally {
			loading = false;
		}
	}

	async function loadPoints() {
		if (!session.user) return;
		const seasonId = await findActiveSeasonId();
		if (!seasonId) return;
		try {
			const leaderboard = await getLeaderboard(seasonId);
			const index = leaderboard.findIndex((entry) => entry.user_id === session.user?.id);
			if (index >= 0) {
				points = leaderboard[index].points;
				rank = index + 1;
			}
		} catch {
			/* el ranking no es crítico para esta vista; se omite en silencio si falla */
		}
	}

	$effect(() => {
		loadMatches();
		loadPoints();
	});

	function toggle(matchId: string) {
		expandedId = expandedId === matchId ? null : matchId;
	}

	function onPredictionSaved(matchId: string, prediction: PredictionRead) {
		matches = matches.map((match) => (match.id === matchId ? { ...match, my_prediction: prediction } : match));
	}

	function onBetPlaced(matchId: string, bet: BetRead) {
		matches = matches.map((match) =>
			match.id === matchId ? { ...match, my_bets: [...match.my_bets, bet] } : match
		);
	}
</script>

<svelte:head>
	<title>Próximos partidos — Quinielas</title>
</svelte:head>

<div class="flex flex-col gap-5">
	<PointsCreditsHeader {points} {rank} balance={session.balance} />

	<h1 class="text-h2 text-text">Próximos partidos</h1>

	{#if loading}
		<p class="text-body-sm text-text-muted">Cargando partidos…</p>
	{:else if loadError}
		<EmptyState
			icon="⊘"
			tone="negative"
			title="No pudimos cargar los partidos"
			description={loadError.message}
		>
			<Button variant="secondary" onclick={loadMatches}>Reintentar</Button>
		</EmptyState>
	{:else if matches.length === 0}
		<EmptyState
			icon="▢"
			title="No hay partidos próximos"
			description="La jornada abierta no tiene partidos pendientes por ahora. Mientras tanto puedes revisar cómo quedaste."
		>
			<a href="/mis-apuestas"><Button variant="secondary">Ver mi historial</Button></a>
		</EmptyState>
	{:else}
		<div class="flex flex-col gap-3.5">
			{#each matches as match (match.id)}
				{@const state = deriveMatchState(match)}
				<MatchCard {match} expanded={expandedId === match.id} ontoggle={() => toggle(match.id)}>
					<PredictionBlock
						matchId={match.id}
						prediction={match.my_prediction}
						disabled={!isBettable(state)}
						onsaved={(prediction) => onPredictionSaved(match.id, prediction)}
					/>
					<OutcomeBetBlock
						matchId={match.id}
						homeLabel={match.home_team_name.slice(0, 3).toUpperCase()}
						awayLabel={match.away_team_name.slice(0, 3).toUpperCase()}
						oddsHome={Number(match.odds_home)}
						oddsDraw={Number(match.odds_draw)}
						oddsAway={Number(match.odds_away)}
						disabled={!isBettable(state)}
						onplaced={(bet) => onBetPlaced(match.id, bet)}
					/>
					<GoalBandBlock
						matchId={match.id}
						homeTeamId={match.home_team_id}
						homeLabel={match.home_team_name}
						awayTeamId={match.away_team_id}
						awayLabel={match.away_team_name}
						goalBandOdds={match.goal_band_odds}
						disabled={!isBettable(state)}
						onplaced={(bet) => onBetPlaced(match.id, bet)}
					/>
				</MatchCard>
			{/each}
		</div>
	{/if}
</div>

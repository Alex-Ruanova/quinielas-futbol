<script lang="ts">
	import type { Snippet } from 'svelte';
	import TeamRow from '$lib/components/TeamRow.svelte';
	import Countdown from '$lib/components/Countdown.svelte';
	import type { MatchUpcoming } from '../_api/matches';
	import { deriveMatchState, type MatchUiState } from '../_lib/matchState';
	import { formatKickoff } from '../_lib/localTime';

	let {
		match,
		expanded = false,
		ontoggle,
		result,
		children
	}: {
		match: MatchUpcoming;
		expanded?: boolean;
		ontoggle?: () => void;
		/** Marcador final; solo disponible cuando el partido ya se liquidó y alguien lo trae aparte
		 * (`MatchUpcomingRead` no incluye score — desaparece de `/matches/upcoming` al liquidarse). */
		result?: { homeScore: number; awayScore: number } | null;
		children?: Snippet;
	} = $props();

	let now = $state(Date.now());

	$effect(() => {
		const id = setInterval(() => {
			now = Date.now();
		}, 1000);
		return () => clearInterval(id);
	});

	const uiState: MatchUiState = $derived(deriveMatchState(match, now));

	const oddsPreviewMuted = $derived(uiState === 'cerrado' || uiState === 'liquidado');

	const predictionLabel = $derived(
		match.my_prediction
			? `${match.my_prediction.predicted_home_score}–${match.my_prediction.predicted_away_score}`
			: 'sin capturar'
	);

	const cardTone: Record<MatchUiState, string> = {
		abierto: 'border-border bg-surface-2',
		'por-cerrar': 'border-status-pending bg-urgent-surface shadow-elev-urgent',
		cerrado: 'border-border bg-surface-1 opacity-90',
		liquidado: 'border-border bg-surface-2'
	};
</script>

<div class="flex flex-col gap-3.5 rounded-2xl border p-4 {cardTone[uiState]}">
	<div class="flex items-center justify-between gap-2">
		<span class="text-label uppercase text-text-muted">{formatKickoff(match.kickoff_at)}</span>
		{#if uiState === 'liquidado'}
			<span class="text-label uppercase text-text-faint">Finalizado</span>
		{:else}
			<Countdown deadline={match.kickoff_at} />
		{/if}
	</div>

	<div class="flex flex-col gap-2.5">
		<TeamRow
			name={match.home_team_name}
			shortCode={match.home_team_name.slice(0, 3).toUpperCase()}
			score={result ? result.homeScore : undefined}
		/>
		<TeamRow
			name={match.away_team_name}
			shortCode={match.away_team_name.slice(0, 3).toUpperCase()}
			score={result ? result.awayScore : undefined}
		/>
	</div>

	<div class="flex gap-2" class:opacity-45={oddsPreviewMuted}>
		{#each [
			[match.home_team_name.slice(0, 3).toUpperCase(), match.odds_home],
			['EMPATE', match.odds_draw],
			[match.away_team_name.slice(0, 3).toUpperCase(), match.odds_away]
		] as [label, odds] (label)}
			<div class="num flex flex-1 flex-col gap-0.5 rounded-xl border border-border-strong bg-surface-1 px-3 py-2.5">
				<span class="text-label uppercase text-text-muted">{label}</span>
				<span class="text-num-md text-text">{Number(odds).toFixed(2)}</span>
			</div>
		{/each}
	</div>

	{#if uiState === 'por-cerrar'}
		<div class="rounded-lg bg-urgent-surface px-3 py-2.5 text-body-sm font-bold text-status-pending">
			Últimos minutos para apostar en este partido.
		</div>
	{/if}

	{#if uiState === 'cerrado'}
		<p class="text-body-sm text-text-muted">
			El partido ya arrancó: pronóstico y apuestas quedaron cerrados.
		</p>
	{/if}

	<button
		type="button"
		onclick={ontoggle}
		class="flex items-center justify-between gap-2 border-t border-border pt-3 text-left"
	>
		<span class="num text-body-sm font-semibold text-text-muted">
			Pronóstico: <span class="text-text">{predictionLabel}</span>
		</span>
		<span class="text-body-sm font-bold text-accent">
			{expanded ? 'Ocultar detalle ↑' : 'Franja de gol →'}
		</span>
	</button>

	<span class="text-label uppercase text-text-faint">Estado: {uiState.replace('-', ' ')}</span>

	{#if expanded && children}
		<div class="flex flex-col gap-4 border-t border-border pt-4">
			{@render children()}
		</div>
	{/if}
</div>

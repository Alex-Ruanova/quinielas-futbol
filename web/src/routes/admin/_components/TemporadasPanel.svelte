<script lang="ts">
	import { onMount } from 'svelte';
	import Card from '$lib/components/Card.svelte';
	import Field from '$lib/components/Field.svelte';
	import Button from '$lib/components/Button.svelte';
	import { ApiError } from '$lib/api/client';
	import {
		createMatch,
		createRound,
		createSeason,
		listMatches,
		listRounds,
		listSeasons,
		listTeams,
		updateScoring
	} from '../_lib/api';
	import type { Match, Round, Season, Team } from '../_lib/api';
	import { GOAL_BANDS } from '../_lib/bands';

	const DEFAULT_POINTS = { outcome: 3, exact_score: 5, goal_band: 2 };
	const DEFAULT_BAND_ODDS = '4.50';

	let seasons = $state<Season[]>([]);
	let teams = $state<Team[]>([]);
	let loadError = $state('');

	let selectedSeasonId = $state<string | null>(null);
	let rounds = $state<Round[]>([]);
	let matchesByRound = $state<Record<string, Match[]>>({});
	let selectedRoundId = $state<string | null>(null);

	let seasonForm = $state({ name: '', starts_on: '', ends_on: '' });
	let seasonFormOpen = $state(false);
	let seasonSaving = $state(false);
	let seasonError = $state('');

	let roundForm = $state({ number: 1, name: '', opens_at: '', closes_at: '' });
	let roundFormOpen = $state(false);
	let roundSaving = $state(false);
	let roundError = $state('');

	let matchForm = $state({ home_team_id: '', away_team_id: '', kickoff_at: '' });
	let matchSaving = $state(false);
	let matchError = $state('');

	let scoringForm = $state({
		outcome: DEFAULT_POINTS.outcome,
		exact_score: DEFAULT_POINTS.exact_score,
		goal_band: DEFAULT_POINTS.goal_band,
		bandOdds: Object.fromEntries(GOAL_BANDS.map((b) => [b.value, DEFAULT_BAND_ODDS])) as Record<
			string,
			string
		>
	});
	let scoringSaving = $state(false);
	let scoringError = $state('');
	let scoringOk = $state(false);

	const selectedSeason = $derived(seasons.find((s) => s.id === selectedSeasonId) ?? null);
	const selectedRoundMatches = $derived(
		selectedRoundId ? matchesByRound[selectedRoundId] ?? [] : []
	);

	function teamName(teamId: string): string {
		return teams.find((t) => t.id === teamId)?.name ?? '?';
	}

	function roundIsSettled(roundId: string): boolean {
		const roundMatches = matchesByRound[roundId] ?? [];
		return roundMatches.length > 0 && roundMatches.every((m) => m.status !== 'SCHEDULED');
	}

	async function loadInitial() {
		try {
			[seasons, teams] = await Promise.all([listSeasons(), listTeams()]);
			if (seasons.length > 0) await selectSeason(seasons[0].id);
		} catch (error) {
			loadError = error instanceof ApiError ? error.message : 'No se pudo cargar la información.';
		}
	}

	onMount(loadInitial);

	async function selectSeason(seasonId: string) {
		selectedSeasonId = seasonId;
		selectedRoundId = null;
		seasonError = '';
		scoringOk = false;
		syncScoringForm();
		try {
			rounds = await listRounds(seasonId);
			const entries = await Promise.all(
				rounds.map(async (round) => [round.id, await listMatches(round.id)] as const)
			);
			matchesByRound = Object.fromEntries(entries);
		} catch (error) {
			loadError = error instanceof ApiError ? error.message : 'No se pudieron cargar las jornadas.';
		}
	}

	function syncScoringForm() {
		const config = (selectedSeason?.scoring_config ?? {}) as Record<string, unknown>;
		const oddsMap = (config.goal_band_odds ?? {}) as Record<string, unknown>;
		scoringForm = {
			outcome: Number(config.outcome ?? DEFAULT_POINTS.outcome),
			exact_score: Number(config.exact_score ?? DEFAULT_POINTS.exact_score),
			goal_band: Number(config.goal_band ?? DEFAULT_POINTS.goal_band),
			bandOdds: Object.fromEntries(
				GOAL_BANDS.map((band) => [band.value, String(oddsMap[band.value] ?? DEFAULT_BAND_ODDS)])
			)
		};
	}

	async function onCreateSeason(event: SubmitEvent) {
		event.preventDefault();
		seasonSaving = true;
		seasonError = '';
		try {
			const created = await createSeason({
				name: seasonForm.name,
				starts_on: seasonForm.starts_on,
				ends_on: seasonForm.ends_on
			});
			seasons = [...seasons, created];
			seasonForm = { name: '', starts_on: '', ends_on: '' };
			seasonFormOpen = false;
			await selectSeason(created.id);
		} catch (error) {
			seasonError = error instanceof ApiError ? error.message : 'No se pudo crear la temporada.';
		} finally {
			seasonSaving = false;
		}
	}

	async function onCreateRound(event: SubmitEvent) {
		event.preventDefault();
		if (!selectedSeasonId) return;
		roundSaving = true;
		roundError = '';
		try {
			const created = await createRound({
				season_id: selectedSeasonId,
				number: roundForm.number,
				name: roundForm.name,
				opens_at: new Date(roundForm.opens_at).toISOString(),
				closes_at: new Date(roundForm.closes_at).toISOString()
			});
			rounds = [...rounds, created];
			matchesByRound = { ...matchesByRound, [created.id]: [] };
			roundForm = { number: rounds.length + 1, name: '', opens_at: '', closes_at: '' };
			roundFormOpen = false;
		} catch (error) {
			roundError = error instanceof ApiError ? error.message : 'No se pudo crear la jornada.';
		} finally {
			roundSaving = false;
		}
	}

	function selectRound(roundId: string) {
		selectedRoundId = roundId;
		matchError = '';
		matchForm = { home_team_id: '', away_team_id: '', kickoff_at: '' };
	}

	async function onCreateMatch(event: SubmitEvent) {
		event.preventDefault();
		if (!selectedRoundId) return;
		matchSaving = true;
		matchError = '';
		try {
			const created = await createMatch({
				round_id: selectedRoundId,
				home_team_id: matchForm.home_team_id,
				away_team_id: matchForm.away_team_id,
				kickoff_at: new Date(matchForm.kickoff_at).toISOString()
			});
			matchesByRound = {
				...matchesByRound,
				[selectedRoundId]: [...(matchesByRound[selectedRoundId] ?? []), created]
			};
			matchForm = { home_team_id: '', away_team_id: '', kickoff_at: '' };
		} catch (error) {
			matchError =
				error instanceof ApiError
					? error.message
					: 'No se pudo crear el partido. Revisa que el horario caiga dentro de la ventana de la jornada.';
		} finally {
			matchSaving = false;
		}
	}

	async function onSaveScoring(event: SubmitEvent) {
		event.preventDefault();
		if (!selectedSeasonId) return;
		scoringSaving = true;
		scoringError = '';
		scoringOk = false;
		try {
			const updated = await updateScoring(selectedSeasonId, {
				outcome: scoringForm.outcome,
				exact_score: scoringForm.exact_score,
				goal_band: scoringForm.goal_band,
				goal_band_odds: scoringForm.bandOdds
			});
			seasons = seasons.map((s) => (s.id === selectedSeasonId ? updated : s));
			scoringOk = true;
		} catch (error) {
			scoringError =
				error instanceof ApiError ? error.message : 'No se pudo guardar la configuración de puntos.';
		} finally {
			scoringSaving = false;
		}
	}
</script>

<div class="flex flex-col gap-5">
	<Card>
		<h2 class="text-h3 text-text">Temporadas, jornadas y partidos</h2>
		{#if loadError}
			<p class="mt-3 text-body-sm font-semibold text-negative">{loadError}</p>
		{/if}

		<div class="mt-4 flex flex-wrap gap-2.5">
			{#each seasons as season (season.id)}
				<button
					type="button"
					onclick={() => selectSeason(season.id)}
					class="min-h-11 rounded-full px-3.5 py-1.5 text-body-sm font-bold {selectedSeasonId ===
					season.id
						? 'bg-accent text-accent-ink'
						: 'border border-border bg-surface-1 text-text-muted'}"
				>
					{season.name}
				</button>
			{/each}
			<button
				type="button"
				onclick={() => (seasonFormOpen = !seasonFormOpen)}
				class="min-h-11 rounded-full border border-dashed border-border-strong bg-surface-1 px-3.5 py-1.5 text-body-sm font-bold text-text-muted hover:border-accent hover:text-accent"
			>
				+ Nueva temporada
			</button>
		</div>

		{#if seasonFormOpen}
			<form class="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3" onsubmit={onCreateSeason}>
				<Field label="Nombre" name="season-name" required bind:value={seasonForm.name} />
				<Field label="Inicia" name="starts-on" type="date" required bind:value={seasonForm.starts_on} />
				<Field label="Termina" name="ends-on" type="date" required bind:value={seasonForm.ends_on} />
				{#if seasonError}
					<p class="col-span-full text-body-sm font-semibold text-negative">{seasonError}</p>
				{/if}
				<Button type="submit" variant="primary" disabled={seasonSaving} class="col-span-full">
					{seasonSaving ? 'Creando…' : 'Crear temporada'}
				</Button>
			</form>
		{/if}

		{#if selectedSeason}
			<div class="mt-6 flex flex-col gap-2">
				<div
					class="grid grid-cols-[80px_1fr_130px_120px] px-1 text-label uppercase text-text-muted"
				>
					<span>Jornada</span>
					<span>Partidos</span>
					<span class="text-right">Cierre</span>
					<span class="text-right">Estado</span>
				</div>
				{#each rounds as round (round.id)}
					{@const roundMatches = matchesByRound[round.id] ?? []}
					{@const settled = roundIsSettled(round.id)}
					<button
						type="button"
						onclick={() => selectRound(round.id)}
						class="grid grid-cols-[80px_1fr_130px_120px] items-center rounded-lg border px-3 py-2.5 text-left text-body-sm {selectedRoundId ===
						round.id
							? 'border-accent bg-surface-3'
							: 'border-border bg-surface-1'}"
					>
						<span class="num font-extrabold text-text">{round.name}</span>
						<span class="text-text-muted">{roundMatches.length} partidos</span>
						<span class="num text-right text-text-muted">
							{new Date(round.closes_at).toLocaleString('es-MX', {
								day: '2-digit',
								month: 'short',
								hour: '2-digit',
								minute: '2-digit'
							})}
						</span>
						<span class="text-right">
							{#if settled}
								<span class="rounded-md bg-status-won-bg px-2.5 py-0.5 text-caption font-extrabold text-status-won-text">
									✓ Liquidada
								</span>
							{:else}
								<span class="rounded-full border border-dashed border-status-pending px-2.5 py-0.5 text-caption font-bold text-status-pending">
									◷ Abierta
								</span>
							{/if}
						</span>
					</button>
				{/each}

				<button
					type="button"
					onclick={() => (roundFormOpen = !roundFormOpen)}
					class="min-h-11 rounded-lg border border-dashed border-border-strong px-3 py-2 text-body-sm font-bold text-text-muted hover:border-accent hover:text-accent"
				>
					+ Agregar jornada
				</button>

				{#if roundFormOpen}
					<form class="grid grid-cols-1 gap-3 rounded-lg border border-border bg-surface-1 p-3 md:grid-cols-4" onsubmit={onCreateRound}>
						<label class="flex flex-col gap-1.5">
						<span class="text-label uppercase text-text-muted">Número</span>
						<input
							type="number"
							min="1"
							required
							bind:value={roundForm.number}
							class="num min-h-11 rounded-lg border border-border-strong bg-surface-1 px-3 py-2 text-body text-text"
						/>
					</label>
						<Field label="Nombre" name="round-name" required bind:value={roundForm.name} />
						<Field label="Abre" name="opens-at" type="datetime-local" required bind:value={roundForm.opens_at} />
						<Field label="Cierra" name="closes-at" type="datetime-local" required bind:value={roundForm.closes_at} />
						{#if roundError}
							<p class="col-span-full text-body-sm font-semibold text-negative">{roundError}</p>
						{/if}
						<Button type="submit" variant="primary" disabled={roundSaving} class="col-span-full">
							{roundSaving ? 'Creando…' : 'Crear jornada'}
						</Button>
					</form>
				{/if}
			</div>
		{/if}

		{#if selectedRoundId}
			<div class="mt-6 flex flex-col gap-3 border-t border-border pt-4">
				<h3 class="text-body-lg font-bold text-text">Partidos de la jornada</h3>
				<ul class="flex flex-col gap-1.5">
					{#each selectedRoundMatches as match (match.id)}
						<li class="flex items-center justify-between rounded-lg border border-border bg-surface-1 px-3 py-2 text-body-sm text-text">
							<span>{teamName(match.home_team_id)} – {teamName(match.away_team_id)}</span>
							<span class="num text-text-muted">
								{new Date(match.kickoff_at).toLocaleString('es-MX', {
									day: '2-digit',
									month: 'short',
									hour: '2-digit',
									minute: '2-digit'
								})}
							</span>
						</li>
					{/each}
				</ul>

				<form class="grid grid-cols-1 gap-3 md:grid-cols-4" onsubmit={onCreateMatch}>
					<label class="flex flex-col gap-1.5">
						<span class="text-label uppercase text-text-muted">Local</span>
						<select
							bind:value={matchForm.home_team_id}
							required
							class="min-h-11 rounded-lg border border-border-strong bg-surface-1 px-3 py-2 text-body text-text"
						>
							<option value="" disabled>Elige equipo</option>
							{#each teams as team (team.id)}
								<option value={team.id}>{team.name}</option>
							{/each}
						</select>
					</label>
					<label class="flex flex-col gap-1.5">
						<span class="text-label uppercase text-text-muted">Visitante</span>
						<select
							bind:value={matchForm.away_team_id}
							required
							class="min-h-11 rounded-lg border border-border-strong bg-surface-1 px-3 py-2 text-body text-text"
						>
							<option value="" disabled>Elige equipo</option>
							{#each teams as team (team.id)}
								<option value={team.id}>{team.name}</option>
							{/each}
						</select>
					</label>
					<Field label="Kickoff" name="kickoff" type="datetime-local" required bind:value={matchForm.kickoff_at} />
					<Button type="submit" variant="primary" disabled={matchSaving} class="self-end">
						{matchSaving ? 'Creando…' : '+ Agregar partido'}
					</Button>
				</form>
				{#if matchError}
					<p class="text-body-sm font-semibold text-negative" role="alert">{matchError}</p>
				{/if}
			</div>
		{/if}
	</Card>

	{#if selectedSeason}
		<Card>
			<h2 class="text-h3 text-text">Configuración de puntos — {selectedSeason.name}</h2>
			<form class="mt-4 flex flex-col gap-5" onsubmit={onSaveScoring}>
				<div class="grid grid-cols-1 gap-3 md:grid-cols-3">
					<label class="flex flex-col gap-1.5">
						<span class="text-label uppercase text-text-muted">Puntos por resultado</span>
						<input
							type="number"
							min="0"
							bind:value={scoringForm.outcome}
							class="num min-h-11 rounded-lg border border-border-strong bg-surface-1 px-3 py-2 text-body text-text"
						/>
					</label>
					<label class="flex flex-col gap-1.5">
						<span class="text-label uppercase text-text-muted">Puntos por marcador exacto</span>
						<input
							type="number"
							min="0"
							bind:value={scoringForm.exact_score}
							class="num min-h-11 rounded-lg border border-border-strong bg-surface-1 px-3 py-2 text-body text-text"
						/>
					</label>
					<label class="flex flex-col gap-1.5">
						<span class="text-label uppercase text-text-muted">Puntos por franja de gol</span>
						<input
							type="number"
							min="0"
							bind:value={scoringForm.goal_band}
							class="num min-h-11 rounded-lg border border-border-strong bg-surface-1 px-3 py-2 text-body text-text"
						/>
					</label>
				</div>

				<div class="flex flex-col gap-2">
					<span class="text-label uppercase text-text-muted">Momio por franja (default del motor: 4.50)</span>
					<div class="grid grid-cols-2 gap-3 md:grid-cols-3">
						{#each GOAL_BANDS as band (band.value)}
							<label class="flex flex-col gap-1.5">
								<span class="num text-caption font-bold text-text-muted">{band.label}</span>
								<input
									type="number"
									step="0.01"
									min="1.01"
									bind:value={scoringForm.bandOdds[band.value]}
									class="num min-h-11 rounded-lg border border-border-strong bg-surface-1 px-3 py-2 text-body text-text"
								/>
							</label>
						{/each}
					</div>
				</div>

				{#if scoringError}
					<p class="text-body-sm font-semibold text-negative" role="alert">{scoringError}</p>
				{/if}
				{#if scoringOk}
					<p class="text-body-sm font-semibold text-positive">Configuración guardada.</p>
				{/if}

				<Button type="submit" variant="primary" disabled={scoringSaving}>
					{scoringSaving ? 'Guardando…' : 'Guardar configuración de puntos'}
				</Button>
			</form>
		</Card>
	{/if}
</div>

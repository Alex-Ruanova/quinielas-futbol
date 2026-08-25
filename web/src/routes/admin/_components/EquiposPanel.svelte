<script lang="ts">
	import { onMount } from 'svelte';
	import Card from '$lib/components/Card.svelte';
	import Field from '$lib/components/Field.svelte';
	import Button from '$lib/components/Button.svelte';
	import { ApiError } from '$lib/api/client';
	import { createTeam, listTeams, oddsPreview, updateTeam } from '../_lib/api';
	import type { OddsPreview, Team } from '../_lib/api';

	/** Rival de referencia fijo del artboard E: la mecánica se observa a fuerza constante. */
	const REFERENCE_STRENGTH = 50;
	const DEBOUNCE_MS = 400;

	let teams = $state<Team[]>([]);
	let loadError = $state('');
	let selectedId = $state<string | null>(null);

	let form = $state({ name: '', strength: 50, crest_url: '' });
	let saving = $state(false);
	let saveError = $state('');
	let saveOk = $state(false);

	let preview = $state<OddsPreview | null>(null);
	let previewLoading = $state(false);
	let previewError = $state('');

	let debounceTimer: ReturnType<typeof setTimeout> | null = null;

	const selectedTeam = $derived(teams.find((team) => team.id === selectedId) ?? null);
	const isCreating = $derived(selectedId === null);

	const impliedProbability = $derived.by(() => {
		if (!preview) return null;
		const odds = Number(preview.odds_home);
		return odds > 0 ? Math.round((1 / odds) * 100) : null;
	});

	/** Escala puramente visual de la barra a partir del momio devuelto por el backend; no es la fórmula de R1. */
	const barWidthPct = $derived.by(() => {
		if (!preview) return 100;
		const odds = Number(preview.odds_home);
		const shrink = Math.min(100, Math.max(0, ((odds - 1) / 4) * 100));
		return Math.round(shrink);
	});

	async function loadTeams() {
		try {
			teams = await listTeams();
		} catch (error) {
			loadError = error instanceof ApiError ? error.message : 'No se pudieron cargar los equipos.';
		}
	}

	onMount(loadTeams);

	function selectTeam(team: Team) {
		selectedId = team.id;
		form = { name: team.name, strength: team.strength, crest_url: team.crest_url ?? '' };
		saveError = '';
		saveOk = false;
		void loadPreview(team.id);
	}

	function startNewTeam() {
		selectedId = null;
		form = { name: '', strength: 50, crest_url: '' };
		preview = null;
		saveError = '';
		saveOk = false;
	}

	async function loadPreview(teamId: string) {
		previewLoading = true;
		previewError = '';
		try {
			preview = await oddsPreview(teamId, REFERENCE_STRENGTH);
		} catch (error) {
			previewError =
				error instanceof ApiError ? error.message : 'No se pudo calcular el momio en vivo.';
		} finally {
			previewLoading = false;
		}
	}

	function onStrengthInput(value: number) {
		form.strength = value;
		if (!selectedId) return;
		const teamId = selectedId;
		if (debounceTimer) clearTimeout(debounceTimer);
		debounceTimer = setTimeout(() => {
			void applyStrengthLive(teamId, value);
		}, DEBOUNCE_MS);
	}

	/** La fuerza se persiste al soltar el slider para que el momio en vivo venga siempre del motor real. */
	async function applyStrengthLive(teamId: string, strength: number) {
		previewLoading = true;
		previewError = '';
		try {
			const updated = await updateTeam(teamId, { strength });
			teams = teams.map((team) => (team.id === teamId ? updated : team));
			preview = await oddsPreview(teamId, REFERENCE_STRENGTH);
		} catch (error) {
			previewError =
				error instanceof ApiError ? error.message : 'No se pudo calcular el momio en vivo.';
		} finally {
			previewLoading = false;
		}
	}

	async function onSubmit(event: SubmitEvent) {
		event.preventDefault();
		saving = true;
		saveError = '';
		saveOk = false;
		try {
			const payload = {
				name: form.name,
				strength: form.strength,
				crest_url: form.crest_url || null
			};
			if (isCreating) {
				const created = await createTeam(payload);
				teams = [...teams, created];
				selectedId = created.id;
			} else if (selectedId) {
				const updated = await updateTeam(selectedId, payload);
				teams = teams.map((team) => (team.id === selectedId ? updated : team));
			}
			saveOk = true;
			if (selectedId) await loadPreview(selectedId);
		} catch (error) {
			saveError = error instanceof ApiError ? error.message : 'No se pudo guardar el equipo.';
		} finally {
			saving = false;
		}
	}
</script>

<div class="grid grid-cols-1 gap-5 md:grid-cols-[280px_1fr]">
	<Card>
		<div class="flex items-baseline justify-between">
			<h2 class="text-h3 text-text">Equipos</h2>
			<button type="button" class="text-body-sm font-bold text-accent-text" onclick={startNewTeam}>
				+ Nuevo
			</button>
		</div>
		{#if loadError}
			<p class="mt-3 text-body-sm font-semibold text-negative">{loadError}</p>
		{/if}
		<ul class="mt-4 flex flex-col gap-2">
			{#each teams as team (team.id)}
				<li>
					<button
						type="button"
						onclick={() => selectTeam(team)}
						class="flex min-h-11 w-full items-center justify-between rounded-lg border px-3 py-2 text-left text-body-sm {selectedId ===
						team.id
							? 'border-accent bg-surface-3 text-text'
							: 'border-border bg-surface-1 text-text-muted hover:border-border-strong'}"
					>
						<span class="font-semibold text-text">{team.name}</span>
						<span class="num text-num-sm">{team.strength}</span>
					</button>
				</li>
			{/each}
		</ul>
	</Card>

	<Card>
		<div class="flex items-baseline justify-between">
			<h2 class="text-h3 text-text">
				{isCreating ? 'Nuevo equipo' : `Equipo · ${selectedTeam?.name ?? ''}`}
			</h2>
			<span class="text-caption text-text-muted">rival de referencia: fuerza {REFERENCE_STRENGTH}</span>
		</div>

		<form class="mt-4 flex flex-col gap-5" onsubmit={onSubmit}>
			<div class="grid grid-cols-1 gap-3 md:grid-cols-2">
				<Field label="Nombre" name="name" required bind:value={form.name} />
				<Field label="Escudo (URL, opcional)" name="crest_url" bind:value={form.crest_url} />
			</div>

			<div class="flex flex-col gap-3">
				<div class="flex items-baseline justify-between">
					<span class="text-label uppercase text-text-muted">Fuerza (strength)</span>
					<span class="num text-num-lg text-accent">{form.strength}</span>
				</div>
				<input
					type="range"
					min="1"
					max="100"
					value={form.strength}
					oninput={(event) => onStrengthInput(Number((event.target as HTMLInputElement).value))}
					class="h-9 w-full accent-[var(--color-accent)]"
				/>
				<div class="num flex justify-between text-caption text-text-faint">
					<span>1 · débil</span>
					<span>50 · promedio</span>
					<span>100 · potencia</span>
				</div>
				{#if isCreating}
					<p class="text-caption text-text-faint">
						Guarda el equipo para ver el momio en vivo contra el rival de referencia.
					</p>
				{/if}
			</div>

			{#if selectedId}
				<div class="flex flex-col gap-3 rounded-2xl border border-border-strong bg-surface-1 p-4">
					<span class="text-label uppercase text-text-muted">
						Momio resultante contra el rival de referencia
					</span>
					{#if previewError}
						<p class="text-body-sm font-semibold text-negative">{previewError}</p>
					{:else if preview}
						<div class="flex flex-wrap items-end gap-6">
							<div class="flex flex-col gap-0.5">
								<span class="text-caption font-semibold text-text-muted">
									{form.name || 'Este equipo'} gana
								</span>
								<span class="num text-num-xl text-accent">{Number(preview.odds_home).toFixed(2)}</span>
							</div>
							<div class="flex flex-col gap-0.5">
								<span class="text-caption font-semibold text-text-muted">Rival gana</span>
								<span class="num text-num-lg text-text">{Number(preview.odds_away).toFixed(2)}</span>
							</div>
							<div class="ml-auto flex flex-col gap-0.5 text-right">
								<span class="text-caption font-semibold text-text-muted">Probabilidad implícita</span>
								<span class="num text-num-lg text-text">
									{impliedProbability !== null ? `${impliedProbability}%` : '—'}
								</span>
							</div>
						</div>
						<div class="flex flex-col gap-1.5">
							<div class="h-2.5 overflow-hidden rounded-full bg-surface-0">
								<div
									class="h-full rounded-full bg-accent transition-[width]"
									style="width: {barWidthPct}%"
								></div>
							</div>
							<span class="text-caption text-text-faint">
								Más fuerza → el momio baja. Sube el slider y observa la barra encogerse.
							</span>
						</div>
					{:else if previewLoading}
						<p class="text-body-sm text-text-muted">Calculando…</p>
					{/if}
				</div>
			{/if}

			{#if saveError}
				<p class="text-body-sm font-semibold text-negative" role="alert">{saveError}</p>
			{/if}
			{#if saveOk}
				<p class="text-body-sm font-semibold text-positive">Equipo guardado.</p>
			{/if}

			<div class="flex gap-3">
				<Button type="submit" variant="primary" disabled={saving}>
					{saving ? 'Guardando…' : 'Guardar equipo'}
				</Button>
				<Button type="button" variant="secondary" onclick={startNewTeam}>Cancelar</Button>
			</div>
		</form>
	</Card>
</div>

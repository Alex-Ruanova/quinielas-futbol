<script lang="ts">
	import { untrack } from 'svelte';
	import { ApiError } from '$lib/api/client';
	import Button from '$lib/components/Button.svelte';
	import { savePrediction, type PredictionRead } from '../_api/matches';

	let {
		matchId,
		prediction,
		disabled = false,
		onsaved
	}: {
		matchId: string;
		prediction: PredictionRead | null;
		disabled?: boolean;
		onsaved?: (prediction: PredictionRead) => void;
	} = $props();

	let homeScore = $state(untrack(() => prediction?.predicted_home_score.toString() ?? ''));
	let awayScore = $state(untrack(() => prediction?.predicted_away_score.toString() ?? ''));
	let saving = $state(false);
	let errorMessage = $state('');
	let savedJustNow = $state(false);

	function digitsOnly(value: string): string {
		return value.replace(/[^0-9]/g, '').slice(0, 2);
	}

	async function save() {
		errorMessage = '';
		savedJustNow = false;
		const home = Number(homeScore);
		const away = Number(awayScore);
		if (homeScore === '' || awayScore === '' || Number.isNaN(home) || Number.isNaN(away)) {
			errorMessage = 'Captura ambos marcadores.';
			return;
		}
		saving = true;
		try {
			const saved = await savePrediction(matchId, {
				predicted_home_score: home,
				predicted_away_score: away
			});
			savedJustNow = true;
			onsaved?.(saved);
		} catch (error) {
			errorMessage = error instanceof ApiError ? error.message : 'No se pudo guardar el pronóstico.';
		} finally {
			saving = false;
		}
	}
</script>

<div class="flex flex-col gap-2.5 rounded-xl border border-border bg-surface-1 p-3.5">
	<div class="flex items-center justify-between">
		<span class="text-label uppercase text-text-muted">1 · Pronóstico de marcador</span>
	</div>
	<div class="flex items-center gap-2.5">
		<input
			bind:value={homeScore}
			oninput={() => (homeScore = digitsOnly(homeScore))}
			inputmode="numeric"
			aria-label="Marcador local"
			{disabled}
			class="num min-h-11 w-16 rounded-lg border border-border-strong bg-surface-0 text-center text-h3 text-text disabled:text-text-faint"
		/>
		<span class="text-body-lg font-bold text-text-faint">–</span>
		<input
			bind:value={awayScore}
			oninput={() => (awayScore = digitsOnly(awayScore))}
			inputmode="numeric"
			aria-label="Marcador visitante"
			{disabled}
			class="num min-h-11 w-16 rounded-lg border border-border-strong bg-surface-0 text-center text-h3 text-text disabled:text-text-faint"
		/>
		<Button
			variant="secondary"
			class="ml-auto"
			disabled={disabled || saving}
			onclick={save}
		>
			{saving ? 'Guardando…' : 'Guardar'}
		</Button>
	</div>
	<span class="text-caption text-text-faint">Pronosticar no consume créditos.</span>
	{#if errorMessage}
		<p class="text-body-sm font-semibold text-negative" role="alert">{errorMessage}</p>
	{/if}
	{#if savedJustNow}
		<p class="text-body-sm font-semibold text-positive" role="status">Pronóstico guardado.</p>
	{/if}
</div>

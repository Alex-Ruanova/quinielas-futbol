<script lang="ts">
	import type { GoalIn } from '../_lib/api';

	let {
		goals = $bindable([]),
		homeTeam,
		awayTeam
	}: {
		goals: GoalIn[];
		homeTeam: { id: string; name: string };
		awayTeam: { id: string; name: string };
	} = $props();

	function teamName(teamId: string): string {
		return teamId === homeTeam.id ? homeTeam.name : awayTeam.name;
	}

	function addGoal() {
		goals = [...goals, { team_id: homeTeam.id, minute: 1, is_stoppage: false }];
	}

	function removeGoal(index: number) {
		goals = goals.filter((_, i) => i !== index);
	}

	function updateTeam(index: number, teamId: string) {
		goals = goals.map((goal, i) => (i === index ? { ...goal, team_id: teamId } : goal));
	}

	function updateMinute(index: number, minute: number) {
		goals = goals.map((goal, i) => (i === index ? { ...goal, minute } : goal));
	}

	function updateStoppage(index: number, isStoppage: boolean) {
		goals = goals.map((goal, i) => (i === index ? { ...goal, is_stoppage: isStoppage } : goal));
	}
</script>

<div class="flex flex-col gap-2">
	<div
		class="grid grid-cols-[1fr_90px_130px_40px] px-1 text-label uppercase text-text-muted"
	>
		<span>Equipo</span>
		<span class="text-right">Minuto</span>
		<span class="text-center">T. añadido</span>
		<span></span>
	</div>

	{#each goals as goal, index (index)}
		<div
			class="grid grid-cols-[1fr_90px_130px_40px] items-center gap-2 rounded-lg border border-border bg-surface-1 px-3 py-2"
		>
			<select
				value={goal.team_id}
				onchange={(event) => updateTeam(index, (event.target as HTMLSelectElement).value)}
				class="min-h-11 rounded-md border border-border-strong bg-surface-1 px-2 text-body-sm text-text"
			>
				<option value={homeTeam.id}>{homeTeam.name}</option>
				<option value={awayTeam.id}>{awayTeam.name}</option>
			</select>
			<input
				type="number"
				min="1"
				max="130"
				value={goal.minute}
				oninput={(event) => updateMinute(index, Number((event.target as HTMLInputElement).value))}
				class="num min-h-11 rounded-md border border-border-strong bg-surface-1 px-2 text-right text-body-sm text-text"
			/>
			<label class="flex items-center justify-center gap-2 text-body-sm text-text-muted">
				<input
					type="checkbox"
					checked={goal.is_stoppage}
					onchange={(event) => updateStoppage(index, (event.target as HTMLInputElement).checked)}
				/>
				T. añadido
			</label>
			<button
				type="button"
				onclick={() => removeGoal(index)}
				aria-label={`Eliminar gol de ${teamName(goal.team_id)} al minuto ${goal.minute}`}
				class="text-right font-bold text-status-lost-text"
			>
				✕
			</button>
		</div>
	{/each}

	<button
		type="button"
		onclick={addGoal}
		class="min-h-11 rounded-lg border border-dashed border-border-strong px-3 py-2 text-body-sm font-bold text-text-muted hover:border-accent hover:text-accent"
	>
		+ Agregar gol
	</button>
</div>

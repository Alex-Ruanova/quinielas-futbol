<script lang="ts">
	import EquiposPanel from './_components/EquiposPanel.svelte';
	import ResultadosPanel from './_components/ResultadosPanel.svelte';
	import TemporadasPanel from './_components/TemporadasPanel.svelte';

	type Tab = 'equipos' | 'resultados' | 'temporadas';
	const tabs: { id: Tab; label: string }[] = [
		{ id: 'equipos', label: 'Equipos' },
		{ id: 'resultados', label: 'Capturar resultado' },
		{ id: 'temporadas', label: 'Temporadas y jornadas' }
	];

	let active = $state<Tab>('equipos');
</script>

<svelte:head>
	<title>Panel de administración — Quinielas</title>
</svelte:head>

<nav class="flex gap-2 border-b border-border pb-2">
	{#each tabs as tab (tab.id)}
		<button
			type="button"
			onclick={() => (active = tab.id)}
			class="min-h-11 rounded-lg px-4 py-2 text-body-sm font-bold {active === tab.id
				? 'bg-accent text-accent-ink'
				: 'text-text-muted hover:text-text'}"
		>
			{tab.label}
		</button>
	{/each}
</nav>

{#if active === 'equipos'}
	<EquiposPanel />
{:else if active === 'resultados'}
	<ResultadosPanel />
{:else}
	<TemporadasPanel />
{/if}

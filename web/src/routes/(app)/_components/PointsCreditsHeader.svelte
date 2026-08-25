<script lang="ts">
	import Money from '$lib/components/Money.svelte';

	let {
		points,
		rank,
		balance
	}: {
		points: number | null;
		rank: number | null;
		balance: string | number | null;
	} = $props();
</script>

<div class="flex flex-col gap-3">
	<div class="flex flex-wrap gap-3">
		<div class="flex flex-1 flex-col gap-0.5 rounded-xl border border-border bg-surface-2 px-3 py-2.5 min-w-[140px]">
			<span class="text-label uppercase text-text-muted">Puntos</span>
			{#if points !== null}
				<span class="num text-num-md text-text">{points} pts</span>
				<span class="text-caption text-text-faint">{rank !== null ? `ranking #${rank}` : 'sin ranking aún'}</span>
			{:else}
				<span class="text-body-sm text-text-faint">— pts</span>
				<span class="text-caption text-text-faint">ranking no disponible</span>
			{/if}
		</div>
		<div class="flex flex-1 flex-col gap-0.5 rounded-xl border border-accent/30 bg-surface-2 px-3 py-2.5 min-w-[140px]">
			<span class="text-label uppercase text-text-muted">Créditos</span>
			<Money value={balance ?? 0} class="text-num-md" />
			<span class="text-caption text-text-faint">virtuales</span>
		</div>
	</div>
	<p class="text-caption leading-relaxed text-text-faint">
		Dos ejes separados: los puntos vienen de tus pronósticos, los créditos de tus apuestas.
		Pronosticar no consume créditos.
	</p>
</div>

<script lang="ts">
	let {
		name,
		shortCode,
		crestBg = 'var(--color-surface-3)',
		crestColor = 'var(--color-text)',
		score
	}: {
		name: string;
		shortCode: string;
		crestBg?: string;
		crestColor?: string;
		score?: number;
	} = $props();
</script>

<div class="flex items-center justify-between gap-2.5">
	<div class="flex items-center gap-2.5">
		<div
			class="flex h-8 w-8 items-center justify-center rounded-md text-caption font-extrabold"
			style="background:{crestBg}; color:{crestColor}"
		>
			{shortCode}
		</div>
		<span class="text-body-lg font-semibold text-text">{name}</span>
	</div>
	{#if score !== undefined}
		<span class="num text-h3 text-text">{score}</span>
	{/if}
</div>

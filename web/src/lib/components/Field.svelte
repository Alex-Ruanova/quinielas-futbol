<script lang="ts">
	import type { HTMLInputAttributes } from 'svelte/elements';

	let {
		label,
		error,
		value = $bindable(''),
		...rest
	}: { label: string; error?: string; value?: string } & HTMLInputAttributes = $props();
</script>

<label class="flex flex-col gap-1.5">
	<span class="text-label uppercase text-text-muted">{label}</span>
	<input
		bind:value
		{...rest}
		class="min-h-11 rounded-lg border border-border-strong bg-surface-1 px-3 py-2 text-body text-text placeholder:text-text-faint focus-visible:border-accent"
		aria-invalid={error ? 'true' : undefined}
	/>
	{#if error}
		<span class="text-caption font-semibold text-negative">{error}</span>
	{/if}
</label>

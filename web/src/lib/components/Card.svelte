<script lang="ts">
	import type { Snippet } from 'svelte';

	let { class: className = '', children }: { class?: string; children: Snippet } = $props();
</script>

<div class="rounded-2xl border border-border bg-surface-2 p-4 shadow-elev-1 md:p-6 {className}">
	{@render children()}
</div>

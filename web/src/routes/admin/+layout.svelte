<script lang="ts">
	let { children }: { children: import('svelte').Snippet } = $props();
</script>

<svelte:head>
	<title>Panel de administración — Quinielas</title>
</svelte:head>

<div class="flex flex-col gap-6">
	<h1 class="text-h1 text-text">Panel de administración</h1>
	{@render children()}
</div>

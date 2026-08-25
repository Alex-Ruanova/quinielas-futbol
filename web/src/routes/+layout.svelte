<script lang="ts">
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import TopBar from '$lib/components/TopBar.svelte';
	import { session } from '$lib/stores/session.svelte';
	import { refreshBalance } from '$lib/api/wallet';

	let { children } = $props();

	$effect(() => {
		if (session.isAuthenticated) {
			refreshBalance().catch(() => {
				/* apiCall ya maneja 401 (logout + redirect); otros errores no bloquean el layout */
			});
		}
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
</svelte:head>

<div class="min-h-screen bg-surface-0 text-text">
	<TopBar />
	<main class="mx-auto max-w-5xl px-4 py-6 md:px-8">
		{@render children()}
	</main>
</div>

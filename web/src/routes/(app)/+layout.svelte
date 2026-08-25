<script lang="ts">
	import type { Snippet } from 'svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { session } from '$lib/stores/session.svelte';

	let { children }: { children: Snippet } = $props();

	$effect(() => {
		if (!session.isAuthenticated) {
			goto('/login');
		}
	});

	const tabs = [
		{ href: '/partidos', label: 'Partidos' },
		{ href: '/ranking', label: 'Ranking' },
		{ href: '/mis-apuestas', label: 'Historial' },
		{ href: '/saldo', label: 'Saldo' }
	];
</script>

<div class="flex flex-col gap-5">
	<nav class="flex gap-5 border-b border-border pb-3" aria-label="Panel del jugador">
		{#each tabs as tab (tab.href)}
			<a
				href={tab.href}
				class="text-body-sm font-bold tracking-wide"
				class:text-accent={page.url.pathname.startsWith(tab.href)}
				class:text-text-muted={!page.url.pathname.startsWith(tab.href)}
			>
				{tab.label}
			</a>
		{/each}
	</nav>
	{@render children()}
</div>

<script lang="ts">
	import { session } from '$lib/stores/session.svelte';
	import Card from '$lib/components/Card.svelte';
	import Button from '$lib/components/Button.svelte';
</script>

<svelte:head>
	<title>Quinielas de Fútbol</title>
</svelte:head>

<Card class="mx-auto max-w-xl">
	<h1 class="text-h1 text-text">Quinielas de Fútbol</h1>
	<p class="mt-3 text-body text-text-muted">
		Apuesta por resultado y franja de gol en los partidos de la jornada. El panel de próximos
		partidos llega en la siguiente fase.
	</p>

	<div class="mt-6 flex flex-wrap gap-3">
		{#if session.isAuthenticated}
			<a href="/perfil"><Button variant="primary">Ir a mi perfil</Button></a>
		{:else}
			<a href="/register"><Button variant="primary">Crear cuenta</Button></a>
			<a href="/login"><Button variant="secondary">Ya tengo cuenta</Button></a>
		{/if}
	</div>
</Card>

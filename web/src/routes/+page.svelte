<script lang="ts">
	import { goto } from '$app/navigation';
	import { session } from '$lib/stores/session.svelte';
	import Card from '$lib/components/Card.svelte';
	import Button from '$lib/components/Button.svelte';

	/* La raiz no tiene contenido propio: el panel del jugador vive en /partidos,
	 * que es la primera pantalla real de la app. */
	$effect(() => {
		if (session.isAuthenticated) goto('/partidos');
	});
</script>

<svelte:head>
	<title>Quinielas de Fútbol</title>
</svelte:head>

{#if !session.isAuthenticated}
	<Card class="mx-auto max-w-xl">
		<h1 class="text-h1 text-text">Quinielas de Fútbol</h1>
		<p class="mt-3 text-body text-text-muted">
			Pronostica los marcadores de la jornada para subir en el ranking y apuesta créditos
			virtuales al resultado o a la franja de 15 minutos en la que caerá un gol.
		</p>
		<p class="mt-2 text-body-sm text-text-faint">
			Los créditos son virtuales y no canjeables. No hay métodos de pago en la app.
		</p>

		<div class="mt-6 flex flex-wrap gap-3">
			<a href="/register"><Button variant="primary">Crear cuenta</Button></a>
			<a href="/login"><Button variant="secondary">Ya tengo cuenta</Button></a>
		</div>
	</Card>
{/if}

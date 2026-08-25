<script lang="ts">
	import { goto } from '$app/navigation';
	import Card from '$lib/components/Card.svelte';
	import Field from '$lib/components/Field.svelte';
	import Button from '$lib/components/Button.svelte';
	import { login } from '$lib/api/auth';
	import { ApiError } from '$lib/api/client';

	let email = $state('');
	let password = $state('');
	let submitting = $state(false);
	let errorMessage = $state('');

	async function onSubmit(event: SubmitEvent) {
		event.preventDefault();
		submitting = true;
		errorMessage = '';
		try {
			await login(email, password);
			await goto('/');
		} catch (error) {
			errorMessage = error instanceof ApiError ? error.message : 'No se pudo iniciar sesión.';
		} finally {
			submitting = false;
		}
	}
</script>

<svelte:head>
	<title>Iniciar sesión — Quinielas</title>
</svelte:head>

<Card class="mx-auto max-w-md">
	<h1 class="text-h2 text-text">Iniciar sesión</h1>

	<form class="mt-6 flex flex-col gap-4" onsubmit={onSubmit}>
		<Field label="Correo" name="email" type="email" required bind:value={email} />
		<Field label="Contraseña" name="password" type="password" required bind:value={password} />

		{#if errorMessage}
			<p class="text-body-sm font-semibold text-negative" role="alert">{errorMessage}</p>
		{/if}

		<Button type="submit" variant="primary" disabled={submitting}>
			{submitting ? 'Entrando…' : 'Entrar'}
		</Button>
	</form>

	<p class="mt-4 text-body-sm text-text-muted">
		¿No tienes cuenta? <a href="/register" class="font-semibold text-accent-text">Regístrate</a>
	</p>
</Card>

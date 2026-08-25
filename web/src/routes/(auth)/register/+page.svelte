<script lang="ts">
	import { goto } from '$app/navigation';
	import Card from '$lib/components/Card.svelte';
	import Field from '$lib/components/Field.svelte';
	import Button from '$lib/components/Button.svelte';
	import { register } from '$lib/api/auth';
	import { ApiError } from '$lib/api/client';

	let email = $state('');
	let password = $state('');
	let displayName = $state('');
	let submitting = $state(false);
	let errorMessage = $state('');

	async function onSubmit(event: SubmitEvent) {
		event.preventDefault();
		submitting = true;
		errorMessage = '';
		try {
			await register({ email, password, display_name: displayName });
			await goto('/');
		} catch (error) {
			errorMessage = error instanceof ApiError ? error.message : 'No se pudo completar el registro.';
		} finally {
			submitting = false;
		}
	}
</script>

<svelte:head>
	<title>Crear cuenta — Quinielas</title>
</svelte:head>

<Card class="mx-auto max-w-md">
	<h1 class="text-h2 text-text">Crear cuenta</h1>
	<p class="mt-2 text-body-sm text-text-muted">Empiezas con 1000 créditos de saldo inicial.</p>

	<form class="mt-6 flex flex-col gap-4" onsubmit={onSubmit}>
		<Field label="Nombre" name="display_name" type="text" required bind:value={displayName} />
		<Field label="Correo" name="email" type="email" required bind:value={email} />
		<Field
			label="Contraseña"
			name="password"
			type="password"
			required
			minlength={8}
			bind:value={password}
		/>

		{#if errorMessage}
			<p class="text-body-sm font-semibold text-negative" role="alert">{errorMessage}</p>
		{/if}

		<Button type="submit" variant="primary" disabled={submitting}>
			{submitting ? 'Creando…' : 'Crear cuenta'}
		</Button>
	</form>

	<p class="mt-4 text-body-sm text-text-muted">
		¿Ya tienes cuenta? <a href="/login" class="font-semibold text-accent-text">Inicia sesión</a>
	</p>
</Card>

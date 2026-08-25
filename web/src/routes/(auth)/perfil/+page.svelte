<script lang="ts">
	import { goto } from '$app/navigation';
	import Card from '$lib/components/Card.svelte';
	import Field from '$lib/components/Field.svelte';
	import Button from '$lib/components/Button.svelte';
	import Money from '$lib/components/Money.svelte';
	import { session } from '$lib/stores/session.svelte';
	import { updateProfile } from '$lib/api/auth';
	import { ApiError } from '$lib/api/client';

	$effect(() => {
		if (!session.isAuthenticated) {
			goto('/login');
		}
	});

	let displayName = $state(session.user?.displayName ?? '');
	let submitting = $state(false);
	let errorMessage = $state('');
	let successMessage = $state('');

	async function onSubmit(event: SubmitEvent) {
		event.preventDefault();
		submitting = true;
		errorMessage = '';
		successMessage = '';
		try {
			await updateProfile({ display_name: displayName });
			successMessage = 'Perfil actualizado.';
		} catch (error) {
			errorMessage = error instanceof ApiError ? error.message : 'No se pudo actualizar el perfil.';
		} finally {
			submitting = false;
		}
	}
</script>

<svelte:head>
	<title>Mi perfil — Quinielas</title>
</svelte:head>

{#if session.user}
	<Card class="mx-auto max-w-md">
		<h1 class="text-h2 text-text">Mi perfil</h1>

		<dl class="mt-4 flex items-center justify-between border-b border-border pb-4">
			<dt class="text-body-sm text-text-muted">Saldo</dt>
			<dd><Money value={session.balance ?? 0} class="text-num-lg" /></dd>
		</dl>

		<form class="mt-4 flex flex-col gap-4" onsubmit={onSubmit}>
			<Field label="Correo" name="email" type="email" value={session.user.email} disabled />
			<Field label="Nombre" name="display_name" type="text" required bind:value={displayName} />

			{#if errorMessage}
				<p class="text-body-sm font-semibold text-negative" role="alert">{errorMessage}</p>
			{/if}
			{#if successMessage}
				<p class="text-body-sm font-semibold text-positive" role="status">{successMessage}</p>
			{/if}

			<Button type="submit" variant="primary" disabled={submitting}>
				{submitting ? 'Guardando…' : 'Guardar cambios'}
			</Button>
		</form>
	</Card>
{/if}

<script lang="ts">
	import { goto } from '$app/navigation';
	import { session } from '$lib/stores/session.svelte';
	import Money from './Money.svelte';
	import Button from './Button.svelte';

	function logout() {
		session.clear();
		goto('/login');
	}

	function toggleTheme() {
		const root = document.documentElement;
		const next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
		root.setAttribute('data-theme', next);
		try {
			localStorage.setItem('quinielas.theme', next);
		} catch {
			/* localStorage puede no estar disponible (Safari privado); el tema simplemente no persiste */
		}
	}
</script>

<header
	class="sticky top-0 z-10 flex min-h-11 items-center justify-between gap-4 border-b border-border bg-surface-1 px-4 py-3 md:px-8"
>
	<a href="/" class="text-h3 text-text no-underline">Quinielas</a>

	<div class="flex items-center gap-3">
		{#if session.isAuthenticated}
			<Money value={session.balance ?? 0} class="text-num-md" />
			<a href="/perfil" class="text-body-sm font-semibold text-text-muted hover:text-accent">
				{session.user?.displayName}
			</a>
			<Button variant="secondary" onclick={logout}>Salir</Button>
		{:else}
			<a href="/login" class="text-body-sm font-semibold text-text-muted hover:text-accent">
				Entrar
			</a>
			<Button variant="primary" onclick={() => goto('/register')}>Registrarme</Button>
		{/if}
		<button
			type="button"
			onclick={toggleTheme}
			aria-label="Cambiar tema"
			class="flex min-h-11 min-w-11 items-center justify-center rounded-lg border border-border text-body-sm text-text-muted hover:text-accent"
		>
			◐
		</button>
	</div>
</header>

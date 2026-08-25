<script lang="ts">
	import { ApiError } from '$lib/api/client';
	import Button from '$lib/components/Button.svelte';
	import Money from '$lib/components/Money.svelte';

	let {
		error,
		balance,
		stake,
		onLowerStake,
		ondismiss
	}: {
		error: ApiError;
		balance: number;
		stake: number;
		onLowerStake: (maxStake: number) => void;
		ondismiss?: () => void;
	} = $props();

	const missing = $derived(Math.max(0, stake - balance));
</script>

{#if error.status === 402}
	<div class="flex flex-col gap-2 rounded-xl border border-status-pending bg-urgent-surface p-3.5">
		<span
			class="inline-flex w-fit items-center gap-1.5 rounded-full border border-dashed border-status-pending px-2.5 py-1 text-caption font-bold text-status-pending"
		>
			<span aria-hidden="true">◷</span> Saldo insuficiente
		</span>
		<p class="text-body-sm font-extrabold text-text">
			Te faltan <Money value={missing} class="text-body-sm" /> para esta apuesta.
		</p>
		<p class="text-body-sm text-text-muted">
			Tienes <Money value={balance} class="text-body-sm" /> y quieres apostar <Money
				value={stake}
				class="text-body-sm"
			/>. Baja el monto o espera la recarga.
		</p>
		<Button variant="primary" class="w-fit" onclick={() => onLowerStake(balance)}>
			Apostar {balance} cr
		</Button>
	</div>
{:else if error.status === 409}
	<div class="flex flex-col gap-2 rounded-xl border-2 border-status-lost bg-surface-1 p-3.5">
		<span
			class="inline-flex w-fit items-center gap-1.5 rounded-xs border-2 border-status-lost px-2.5 py-1 text-caption font-bold text-status-lost-text"
		>
			<span aria-hidden="true">✕</span> Apuesta rechazada
		</span>
		<p class="text-body-sm font-extrabold text-text">El partido cerró mientras confirmabas</p>
		<p class="text-body-sm text-text-muted">
			No se descontó ningún crédito de tu saldo. Elige otro partido abierto.
		</p>
		{#if ondismiss}
			<Button variant="secondary" class="w-fit" onclick={ondismiss}>Ver otros partidos abiertos</Button>
		{/if}
	</div>
{:else}
	<p class="text-body-sm font-semibold text-negative" role="alert">{error.message}</p>
{/if}

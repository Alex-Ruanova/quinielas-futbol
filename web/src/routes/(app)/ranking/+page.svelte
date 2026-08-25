<script lang="ts">
	import Money from '$lib/components/Money.svelte';
	import { session } from '$lib/stores/session.svelte';
	import { formatMoney } from '$lib/utils/format';
	import { findActiveSeason, getLeaderboard, type LeaderboardEntry, type Season } from '../_api/leaderboard';
	import EmptyState from '../_components/EmptyState.svelte';

	let loading = $state(true);
	let season = $state<Season | null>(null);
	let entries = $state<LeaderboardEntry[]>([]);
	let unavailable = $state(false);

	async function load() {
		loading = true;
		unavailable = false;
		season = await findActiveSeason();
		if (!season) {
			unavailable = true;
			loading = false;
			return;
		}
		try {
			entries = await getLeaderboard(season.id);
		} catch {
			unavailable = true;
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		load();
	});
</script>

<svelte:head>
	<title>Ranking — Quinielas</title>
</svelte:head>

<div class="flex flex-col gap-5">
	<h1 class="text-h2 text-text">Tabla de posiciones{season ? ` · ${season.name}` : ''}</h1>

	{#if loading}
		<p class="text-body-sm text-text-muted">Cargando ranking…</p>
	{:else if unavailable}
		<EmptyState
			icon="⊘"
			tone="void"
			title="El ranking no está disponible ahora"
			description="No pudimos determinar la temporada activa para tu cuenta. Es una limitación conocida de la API para jugadores sin rol de administrador; vuelve a intentarlo más tarde."
		/>
	{:else if entries.length === 0}
		<EmptyState
			icon="▢"
			title="Todavía no hay puntos registrados"
			description="En cuanto se liquide el primer partido de la temporada, la tabla empieza a llenarse."
		/>
	{:else}
		{#if season?.status !== 'closed' && season?.status !== 'finished'}
			<div class="flex flex-col gap-1 rounded-xl border border-dotted border-status-void bg-surface-2 p-3.5">
				<span
					class="inline-flex w-fit items-center gap-1.5 rounded-full border border-dotted border-status-void px-2.5 py-1 text-caption font-bold text-status-void-text"
				>
					<span aria-hidden="true">⊘</span> Sin liquidar
				</span>
				<p class="text-body-sm text-text-muted">
					La temporada aún no cierra. Esta tabla es parcial y puede moverse conforme se liquiden más partidos.
				</p>
			</div>
		{/if}

		<div class="overflow-hidden rounded-2xl border border-border bg-surface-2">
			<div
				class="grid grid-cols-[48px_1fr_80px_80px_100px] gap-2 border-b border-border px-4 py-2.5 text-caption font-extrabold uppercase tracking-wide text-text-muted"
			>
				<span>Pos</span><span>Usuario</span><span class="text-right">Puntos</span><span class="text-right">Exactos</span
				><span class="text-right">Balance cr</span>
			</div>
			{#each entries as entry, index (entry.user_id)}
				{@const isMe = entry.user_id === session.user?.id}
				<div
					class="grid grid-cols-[48px_1fr_80px_80px_100px] items-center gap-2 px-4 py-3 text-body-sm last:border-b-0"
					class:bg-accent={isMe}
					class:text-accent-ink={isMe}
					class:border-b={!isMe}
					class:border-border={!isMe}
				>
					<span class="num font-extrabold" class:text-text-muted={!isMe}>{index + 1}</span>
					<span class="font-semibold">{entry.display_name}{isMe ? ' · tú' : ''}</span>
					<span class="num text-right font-extrabold">{entry.points}</span>
					<span class="num text-right" class:text-text-muted={!isMe}>{entry.exact_scores}</span>
					{#if isMe}
						<span class="num text-right font-extrabold text-accent-ink">{formatMoney(entry.balance, true)}</span>
					{:else}
						<Money value={entry.balance} signed class="justify-self-end text-num-sm" />
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>

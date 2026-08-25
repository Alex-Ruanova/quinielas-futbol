<script lang="ts">
	export type BetStatus = 'pendiente' | 'ganada' | 'perdida' | 'anulada';

	let { status }: { status: BetStatus } = $props();

	/* Cada estado se distingue por color + forma + icono + etiqueta — nunca solo color. */
	const config: Record<BetStatus, { icon: string; label: string; class: string }> = {
		pendiente: {
			icon: '◷',
			label: 'Pendiente',
			class: 'rounded-full border border-dashed border-status-pending text-status-pending'
		},
		ganada: {
			icon: '✓',
			label: 'Ganada',
			class: 'rounded-md bg-status-won-bg text-status-won-text'
		},
		perdida: {
			icon: '✕',
			label: 'Perdida',
			class: 'rounded-xs border-2 border-status-lost text-status-lost-text'
		},
		anulada: {
			icon: '⊘',
			label: 'Anulada',
			class: 'rounded-full border border-dotted border-status-void text-status-void-text'
		}
	};
</script>

<span
	class="inline-flex items-center gap-1.5 px-3 py-1.5 text-body-sm font-bold tracking-wide {config[
		status
	].class}"
>
	<span aria-hidden="true">{config[status].icon}</span>
	<span class:line-through={status === 'anulada'}>{config[status].label}</span>
</span>

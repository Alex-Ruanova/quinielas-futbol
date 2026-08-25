<script lang="ts">
	import type { HTMLButtonAttributes } from 'svelte/elements';

	type OddsState = 'reposo' | 'seleccionado' | 'bloqueado';

	let {
		label,
		odds,
		state = 'reposo',
		...rest
	}: { label: string; odds: number; state?: OddsState } & HTMLButtonAttributes = $props();

	const styles: Record<OddsState, string> = {
		reposo: 'bg-surface-1 border border-border text-text hover:border-accent',
		seleccionado: 'bg-accent border border-accent text-accent-ink',
		bloqueado: 'bg-surface-1 border border-dashed border-border text-text-faint opacity-55'
	};

	const labelTone: Record<OddsState, string> = {
		reposo: 'text-text-muted',
		seleccionado: 'text-accent-ink-soft',
		bloqueado: 'text-text-faint'
	};
</script>

<button
	type="button"
	disabled={state === 'bloqueado'}
	class="flex min-h-11 flex-1 flex-col gap-0.5 rounded-xl px-3 py-2.5 text-left disabled:cursor-not-allowed {styles[
		state
	]}"
	{...rest}
>
	<span class="text-label uppercase {labelTone[state]}">{label}</span>
	<span class="num text-num-md">{odds.toFixed(2)}</span>
</button>

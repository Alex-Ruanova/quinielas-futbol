<script lang="ts">
	import Button from '$lib/components/Button.svelte';

	let {
		open = $bindable(false),
		title,
		description,
		confirmLabel = 'Confirmar',
		onconfirm
	}: {
		open?: boolean;
		title: string;
		description: string;
		confirmLabel?: string;
		onconfirm: () => void;
	} = $props();

	function confirm() {
		open = false;
		onconfirm();
	}
</script>

{#if open}
	<div class="fixed inset-0 z-20 flex items-center justify-center bg-black/60 p-4">
		<div class="w-full max-w-sm rounded-2xl border border-border bg-surface-2 p-6 shadow-elev-2">
			<h2 class="text-h3 text-text">{title}</h2>
			<p class="mt-2 text-body-sm text-text-muted">{description}</p>
			<div class="mt-6 flex justify-end gap-3">
				<Button variant="secondary" onclick={() => (open = false)}>Cancelar</Button>
				<Button variant="primary" onclick={confirm}>{confirmLabel}</Button>
			</div>
		</div>
	</div>
{/if}

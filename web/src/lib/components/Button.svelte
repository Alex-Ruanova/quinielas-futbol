<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { HTMLButtonAttributes } from 'svelte/elements';

	type Variant = 'primary' | 'secondary';

	let {
		variant = 'primary',
		class: className = '',
		children,
		...rest
	}: HTMLButtonAttributes & { variant?: Variant; children: Snippet } = $props();

	const base =
		'inline-flex min-h-11 items-center justify-center gap-2 rounded-lg px-5 py-3 text-body font-bold transition-colors disabled:cursor-not-allowed';

	const variants: Record<Variant, string> = {
		primary:
			'bg-accent text-accent-ink hover:bg-accent-hover disabled:bg-surface-3 disabled:text-text-faint',
		secondary:
			'border border-border-strong text-text hover:border-accent hover:text-accent disabled:border-border disabled:text-text-faint'
	};
</script>

<button {...rest} class="{base} {variants[variant]} {className}">
	{@render children()}
</button>

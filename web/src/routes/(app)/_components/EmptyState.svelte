<script lang="ts">
	import type { Snippet } from 'svelte';

	type Tone = 'neutral' | 'urgent' | 'negative' | 'void';

	let {
		icon = '▢',
		tone = 'neutral',
		title,
		description,
		children
	}: {
		icon?: string;
		tone?: Tone;
		title: string;
		description: string;
		children?: Snippet;
	} = $props();

	const toneBorder: Record<Tone, string> = {
		neutral: 'border-border',
		urgent: 'border-status-pending',
		negative: 'border-2 border-status-lost',
		void: 'border-border'
	};
</script>

<div
	class="flex flex-col gap-2.5 rounded-2xl border bg-surface-2 p-5 {toneBorder[tone]}"
>
	<span class="text-h2 text-text-faint" aria-hidden="true">{icon}</span>
	<span class="text-body-lg font-extrabold text-text">{title}</span>
	<span class="text-body-sm leading-relaxed text-text-muted">{description}</span>
	{#if children}
		<div class="mt-1">
			{@render children()}
		</div>
	{/if}
</div>

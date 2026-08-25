<script lang="ts">
	import { formatMoney } from '$lib/utils/format';

	let {
		value,
		signed = false,
		class: className = ''
	}: { value: number | string; signed?: boolean; class?: string } = $props();

	const numeric = $derived(typeof value === 'string' ? Number(value) : value);
	const tone = $derived(
		!signed ? 'text-text' : numeric > 0 ? 'text-positive' : numeric < 0 ? 'text-negative' : 'text-text'
	);
</script>

<span class="num font-extrabold {tone} {className}">
	{formatMoney(numeric, signed)}
</span>

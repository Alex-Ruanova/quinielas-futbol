<script lang="ts">
	const URGENT_THRESHOLD_MS = 15 * 60 * 1000;

	let { deadline }: { deadline: string | Date } = $props();

	let now = $state(Date.now());
	let prefersReducedMotion = $state(false);

	$effect(() => {
		const id = setInterval(() => {
			now = Date.now();
		}, 1000);
		return () => clearInterval(id);
	});

	$effect(() => {
		const query = window.matchMedia('(prefers-reduced-motion: reduce)');
		prefersReducedMotion = query.matches;
		const onChange = (event: MediaQueryListEvent) => {
			prefersReducedMotion = event.matches;
		};
		query.addEventListener('change', onChange);
		return () => query.removeEventListener('change', onChange);
	});

	function format(ms: number): string {
		const totalSeconds = Math.floor(ms / 1000);
		const hours = Math.floor(totalSeconds / 3600);
		const minutes = Math.floor((totalSeconds % 3600) / 60);
		const seconds = totalSeconds % 60;
		const pad = (n: number) => n.toString().padStart(2, '0');
		return hours > 0 ? `${pad(hours)}:${pad(minutes)}:${pad(seconds)}` : `${pad(minutes)}:${pad(seconds)}`;
	}

	const targetMs = $derived(new Date(deadline).getTime());
	const remainingMs = $derived(Math.max(0, targetMs - now));
	const isClosed = $derived(remainingMs <= 0);
	const isUrgent = $derived(!isClosed && remainingMs <= URGENT_THRESHOLD_MS);
	const label = $derived(isClosed ? 'apuestas cerradas' : `cierra en ${format(remainingMs)}`);
</script>

<span
	class="num inline-flex items-center gap-1.5 rounded-full border border-border px-3 py-1 text-body-sm font-bold text-text-muted"
	class:bg-urgent={isUrgent}
	class:text-accent-ink={isUrgent}
	class:border-transparent={isUrgent}
	class:animate-pulse-urgent={isUrgent && !prefersReducedMotion}
>
	<span aria-hidden="true">◷</span><span>{label}</span>
</span>

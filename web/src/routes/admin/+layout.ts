import { redirect } from '@sveltejs/kit';
import { session } from '$lib/stores/session.svelte';

/** No-admin nunca ve la interfaz a medias: se corta antes de renderizar cualquier panel. */
export function load() {
	if (!session.isAuthenticated || !session.user) {
		redirect(302, '/login');
	}
	if (!session.user.isAdmin) {
		redirect(302, '/');
	}
}

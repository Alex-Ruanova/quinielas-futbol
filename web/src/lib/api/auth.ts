import { apiCall, client } from './client';
import { session } from '$lib/stores/session.svelte';
import { refreshBalance } from './wallet';
import type { components } from './schema';

export type RegisterPayload = components['schemas']['UserRegister'];
export type UserProfile = components['schemas']['UserOut'];
export type ProfileUpdate = components['schemas']['UserUpdate'];

async function loadSessionUser(): Promise<void> {
	const me = await apiCall(client.GET('/api/v1/users/me', {}));
	session.setUser({
		id: me.id,
		email: me.email,
		displayName: me.display_name,
		isAdmin: me.is_admin
	});
	await refreshBalance();
}

export async function login(email: string, password: string): Promise<void> {
	const token = await apiCall(client.POST('/api/v1/auth/login', { body: { email, password } }));
	session.setToken(token.access_token);
	await loadSessionUser();
}

export async function register(payload: RegisterPayload): Promise<void> {
	await apiCall(client.POST('/api/v1/auth/register', { body: payload }));
	await login(payload.email, payload.password);
}

export async function updateProfile(payload: ProfileUpdate): Promise<UserProfile> {
	const updated = await apiCall(client.PATCH('/api/v1/users/me', { body: payload }));
	session.setUser({
		id: updated.id,
		email: updated.email,
		displayName: updated.display_name,
		isAdmin: updated.is_admin
	});
	return updated;
}

export function logout(): void {
	session.clear();
}

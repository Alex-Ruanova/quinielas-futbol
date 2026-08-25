import createClient from 'openapi-fetch';
import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import { session } from '$lib/stores/session.svelte';
import type { paths } from './schema';

/* En produccion la API vive en otro host que la SPA, asi que la URL se inyecta
 * en build. `PUBLIC_` es el prefijo que SvelteKit expone al bundle del cliente. */
export const API_BASE_URL = import.meta.env.PUBLIC_API_URL ?? 'http://localhost:8000';

export type ApiErrorStatus = 401 | 402 | 409 | 422 | 0;

/** Error tipado para cualquier respuesta no-2xx; nunca hay fallo silencioso. */
export class ApiError extends Error {
	constructor(
		public readonly status: ApiErrorStatus,
		message: string,
		public readonly detail?: unknown
	) {
		super(message);
		this.name = 'ApiError';
	}
}

type ValidationDetail = { detail?: Array<{ loc?: unknown[]; msg?: string }> };
type ConflictDetail = { detail?: string };

function validationMessage(body: unknown): string {
	const items = (body as ValidationDetail | undefined)?.detail;
	if (!Array.isArray(items) || items.length === 0) return 'Datos inválidos.';
	return items
		.map((item) => {
			const field = Array.isArray(item.loc) ? item.loc.at(-1) : undefined;
			return field ? `${field}: ${item.msg ?? 'inválido'}` : item.msg ?? 'dato inválido';
		})
		.join(' · ');
}

function conflictMessage(body: unknown): string {
	const raw = (body as ConflictDetail | undefined)?.detail;
	return typeof raw === 'string' ? raw : 'Conflicto: apuestas cerradas o dato ya registrado.';
}

function messageFor(status: number, body: unknown): string {
	switch (status) {
		case 401:
			return 'Tu sesión expiró. Inicia sesión de nuevo.';
		case 402:
			return 'Saldo insuficiente para esta operación.';
		case 409:
			return conflictMessage(body);
		case 422:
			return validationMessage(body);
		default:
			return 'Ocurrió un error inesperado. Intenta de nuevo.';
	}
}

export const client = createClient<paths>({ baseUrl: API_BASE_URL });

client.use({
	onRequest({ request }) {
		if (session.token) {
			request.headers.set('Authorization', `Bearer ${session.token}`);
		}
		return request;
	}
});

/**
 * Desenvuelve la respuesta de openapi-fetch: devuelve `data` en 2xx, o lanza
 * `ApiError` con mensaje legible en español. Un 401 limpia la sesión y redirige a
 * `/login`.
 */
export async function apiCall<D>(
	promise: Promise<{ data?: D; error?: unknown; response: Response }>
): Promise<D> {
	const { data, error, response } = await promise;
	if (response.ok) return data as D;

	const status = response.status as ApiErrorStatus;
	if (status === 401) {
		session.clear();
		if (browser) await goto('/login');
	}
	throw new ApiError(status, messageFor(status, error), error);
}

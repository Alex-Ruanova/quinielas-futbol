import { browser } from '$app/environment';

export type SessionUser = {
	id: string;
	email: string;
	displayName: string;
	isAdmin: boolean;
};

type PersistedSession = {
	token: string;
	user: SessionUser;
};

const STORAGE_KEY = 'quinielas.session';

function readStorage(): PersistedSession | null {
	if (!browser) return null;
	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		return raw ? (JSON.parse(raw) as PersistedSession) : null;
	} catch {
		return null;
	}
}

const initial = readStorage();

let token = $state<string | null>(initial?.token ?? null);
let user = $state<SessionUser | null>(initial?.user ?? null);
let balance = $state<string | null>(null);

function persist() {
	if (!browser) return;
	if (token && user) {
		localStorage.setItem(STORAGE_KEY, JSON.stringify({ token, user } satisfies PersistedSession));
	} else {
		localStorage.removeItem(STORAGE_KEY);
	}
}

/** Sesión compartida en memoria + localStorage; sobrevive a un refresh de página. */
export const session = {
	get token() {
		return token;
	},
	get user() {
		return user;
	},
	get balance() {
		return balance;
	},
	get isAuthenticated() {
		return token !== null;
	},
	setToken(next: string) {
		token = next;
		persist();
	},
	setUser(next: SessionUser) {
		user = next;
		persist();
	},
	setBalance(next: string) {
		balance = next;
	},
	clear() {
		token = null;
		user = null;
		balance = null;
		persist();
	}
};

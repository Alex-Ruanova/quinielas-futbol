import type { BetRead, GoalBand } from '../_api/matches';
import { goalBandLabel } from './goalBands';
import { teamLabel } from './matchLabels';

const OUTCOME_LABEL: Record<string, string> = { HOME: 'Local', DRAW: 'Empate', AWAY: 'Visita' };

/** BetRead.selection llega como `Record<string, unknown>` (el discriminador se perdió al
 * serializar); se reconstruye leyendo `market`/`pick`/`band`/`team_id` a mano. */
export function describeSelection(bet: BetRead): string {
	const selection = bet.selection;
	if (bet.market === 'OUTCOME') {
		const pick = selection.pick;
		return typeof pick === 'string' ? OUTCOME_LABEL[pick] ?? pick : 'Resultado';
	}
	const band = selection.band;
	const bandLabel = typeof band === 'string' ? goalBandLabel(band as GoalBand) : '—';
	const teamId = selection.team_id;
	const team = typeof teamId === 'string' ? teamLabel(bet.match_id, teamId) : null;
	return team ? `${bandLabel} · ${team}` : `Franja ${bandLabel}`;
}

export function marketLabel(bet: BetRead): string {
	return bet.market === 'OUTCOME' ? 'Resultado' : 'Franja de gol';
}

export function payoutFor(bet: BetRead): { amount: number; display: 'money' | 'pending' | 'void' } {
	const stake = Number(bet.stake);
	const odds = Number(bet.odds_snapshot);
	if (bet.status === 'WON') return { amount: Math.round(stake * odds), display: 'money' };
	if (bet.status === 'LOST') return { amount: -stake, display: 'money' };
	if (bet.status === 'VOID') return { amount: stake, display: 'void' };
	return { amount: 0, display: 'pending' };
}


// Same contract as control-sdk-python/src/control_sdk/heartbeat.py

import { State, type ControlState } from "./controlState.ts";

export interface Heartbeat {
  state: State;
  stateVersion: number;
  activeRunId: string | null;
  emittedAt: string; // ISO 8601, UTC
}

export function emitHeartbeat(controlState: ControlState, activeRunId: string | null): Heartbeat {
  return {
    state: controlState.state,
    stateVersion: controlState.stateVersion,
    activeRunId,
    emittedAt: new Date().toISOString(),
  };
}

function ageSeconds(heartbeat: Heartbeat, now: Date): number {
  return (now.getTime() - new Date(heartbeat.emittedAt).getTime()) / 1000;
}

export function isFresh(heartbeat: Heartbeat | null, maxAgeSeconds: number, now: Date = new Date()): boolean {
  if (heartbeat === null) return false;
  return ageSeconds(heartbeat, now) <= maxAgeSeconds;
}

/**
 * What an outside observer (dashboard, reconciler) should treat the
 * agent's state as, right now. CLAUDE.md section 9: "If heartbeat is
 * stale, state is UNKNOWN. Never guess." — a missing or stale heartbeat
 * is reported as UNKNOWN, never as the last state we happened to see.
 */
export function effectiveState(heartbeat: Heartbeat | null, maxAgeSeconds: number, now: Date = new Date()): State {
  if (!isFresh(heartbeat, maxAgeSeconds, now)) return State.UNKNOWN;
  return heartbeat!.state;
}

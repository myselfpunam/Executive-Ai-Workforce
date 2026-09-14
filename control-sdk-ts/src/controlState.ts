// Same contract as control-sdk-python/src/control_sdk/control_state.py —
// this file must stay in lockstep with that one. See CLAUDE.md section 9.
//
// Note on naming: Python methods are snake_case (request_pause), TypeScript
// methods here are camelCase (requestPause) — that's just each language's
// normal convention, not a difference in behavior.

export const State = {
  ACTIVE: "ACTIVE",
  PAUSE_REQUESTED: "PAUSE_REQUESTED",
  PAUSED: "PAUSED",
  RESUME_REQUESTED: "RESUME_REQUESTED",
  STOP_REQUESTED: "STOP_REQUESTED",
  STOPPED: "STOPPED",
  // Not reached by any transition below — set by the heartbeat layer when
  // the last heartbeat is stale. Never guessed.
  UNKNOWN: "UNKNOWN",
} as const;

export type State = (typeof State)[keyof typeof State];

// Any transition not listed here is illegal.
const ALLOWED: Record<State, ReadonlySet<State>> = {
  [State.ACTIVE]: new Set([State.PAUSE_REQUESTED, State.STOP_REQUESTED]),
  [State.PAUSE_REQUESTED]: new Set([State.PAUSED, State.STOP_REQUESTED]),
  [State.PAUSED]: new Set([State.RESUME_REQUESTED, State.STOP_REQUESTED]),
  [State.RESUME_REQUESTED]: new Set([State.ACTIVE]),
  [State.STOP_REQUESTED]: new Set([State.STOPPED]),
  [State.STOPPED]: new Set([State.RESUME_REQUESTED]),
  [State.UNKNOWN]: new Set([]),
};

export class IllegalTransition extends Error {
  constructor(from: State, to: State) {
    super(`cannot go from ${from} to ${to}`);
    this.name = "IllegalTransition";
  }
}

/**
 * In-memory control state for one agent/run. No network, no persistence of
 * its own (see checkpoint.ts) — just the legal-transition logic.
 *
 * stateVersion increments on every successful transition — the same
 * counter the Control API will later use for optimistic concurrency.
 */
export class ControlState {
  state: State = State.ACTIVE;
  stateVersion = 0;

  requestPause(): void {
    this.transition(State.PAUSE_REQUESTED);
  }

  confirmPaused(): void {
    this.transition(State.PAUSED);
  }

  requestStop(): void {
    this.transition(State.STOP_REQUESTED);
  }

  confirmStopped(): void {
    this.transition(State.STOPPED);
  }

  requestResume(): void {
    this.transition(State.RESUME_REQUESTED);
  }

  confirmResumed(): void {
    this.transition(State.ACTIVE);
  }

  isPauseRequested(): boolean {
    return this.state === State.PAUSE_REQUESTED;
  }

  isStopRequested(): boolean {
    return this.state === State.STOP_REQUESTED;
  }

  private transition(target: State): void {
    const allowed = ALLOWED[this.state];
    if (!allowed.has(target)) {
      throw new IllegalTransition(this.state, target);
    }
    this.state = target;
    this.stateVersion += 1;
  }

  /** Rebuild state after a restart, from a checkpoint file — not a
   * transition (no legality check), just restoring a fact that was already
   * true before the process stopped. */
  static fromPersisted(state: State, stateVersion: number): ControlState {
    const cs = new ControlState();
    cs.state = state;
    cs.stateVersion = stateVersion;
    return cs;
  }
}

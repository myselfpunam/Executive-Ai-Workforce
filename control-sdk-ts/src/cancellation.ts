// Same contract as control-sdk-python/src/control_sdk/cancellation.py

import type { ControlState } from "./controlState.ts";

/**
 * Handed to a step's action only if it opts in. Checking isCancelled never
 * mutates controlState — only the safe-point logic in the agent's loop
 * actually confirms a stop. This just lets a long-running operation ask
 * "should I stop?" partway through its own work.
 *
 * CLAUDE.md section 8: "Pass a cancellation token only to components that
 * support it." — an operation that never checks this token will still run
 * to completion; that is correct, not a bug.
 */
export class CancellationToken {
  private controlState: ControlState;

  constructor(controlState: ControlState) {
    this.controlState = controlState;
  }

  get isCancelled(): boolean {
    return this.controlState.isStopRequested();
  }
}

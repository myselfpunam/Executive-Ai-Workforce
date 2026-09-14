// Same contract as control-sdk-python/src/control_sdk/command_inbox.py

export interface CommandResult {
  commandId: string;
  status: string;
  resultingState: string;
  stateVersion: number;
}

/**
 * Delivery is at-least-once (CLAUDE.md section 10) — the same command can
 * legitimately arrive twice (a retry after a slow/lost ack). This
 * remembers every command's result by its immutable commandId, so a
 * repeat delivery gets back the SAME result instead of being applied
 * again — one effect, one audit trail, per CLAUDE.md section 14.
 */
export class CommandInbox {
  private results = new Map<string, CommandResult>();

  handle(commandId: string, apply: () => CommandResult): CommandResult {
    const existing = this.results.get(commandId);
    if (existing) return existing;
    const result = apply();
    this.results.set(commandId, result);
    return result;
  }
}

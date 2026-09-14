// Same contract as control-sdk-python/src/control_sdk/capabilities.py

import { isFresh, type Heartbeat } from "./heartbeat.ts";

/** The "badge" an agent wears, from CLAUDE.md section 12. A real
 * provider-hosted/opaque agent might have all three flags false — that's
 * CONTROL_UNSUPPORTED, not an error. */
export interface Capabilities {
  pauseSupported: boolean;
  stopSupported: boolean;
  resumeSupported: boolean;
  checkpointMode: string;
  maxCheckpointDelayMs: number;
  adapterVersion: string;
}

type Action = "PAUSE" | "STOP" | "RESUME";

const ACTION_FLAG: Record<Action, keyof Capabilities> = {
  PAUSE: "pauseSupported",
  STOP: "stopSupported",
  RESUME: "resumeSupported",
};

/** The UI rule from CLAUDE.md section 12: enable a control only if the
 * capability is supported AND the heartbeat is fresh. (Role and
 * stateVersion checks join this once a real UI/API exist.) */
export function canIssue(
  action: string,
  capabilities: Capabilities,
  heartbeat: Heartbeat | null,
  maxAgeSeconds: number,
  now: Date = new Date(),
): boolean {
  const flagName = ACTION_FLAG[action as Action];
  if (flagName === undefined) return false;
  if (!capabilities[flagName]) return false;
  return isFresh(heartbeat, maxAgeSeconds, now);
}

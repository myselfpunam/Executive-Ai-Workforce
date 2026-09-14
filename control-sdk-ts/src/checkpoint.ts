// Same contract as control-sdk-python/src/control_sdk/checkpoint.py
//
// Deliberately generic: this module knows nothing about any specific
// agent's Run/Step types (agent code depends on control-sdk, never the
// other way around) — it just needs a runId and "which step comes next."

import { readFileSync, writeFileSync } from "node:fs";
import type { ControlState } from "./controlState.ts";

export interface CheckpointData {
  runId: string;
  nextStepIndex: number;
  controlState: string;
  stateVersion: number;
}

/** Write down exactly enough to resume later: which run, which step comes
 * next, and the control state at the moment we stopped. */
export function saveCheckpoint(
  runId: string,
  nextStepIndex: number,
  controlState: ControlState,
  path: string,
): void {
  const data: CheckpointData = {
    runId,
    nextStepIndex,
    controlState: controlState.state,
    stateVersion: controlState.stateVersion,
  };
  writeFileSync(path, JSON.stringify(data, null, 2));
}

export function loadCheckpoint(path: string): CheckpointData {
  return JSON.parse(readFileSync(path, "utf-8")) as CheckpointData;
}

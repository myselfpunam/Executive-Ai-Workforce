import { test } from "node:test";
import assert from "node:assert/strict";

import { ControlState } from "../src/controlState.ts";
import { emitHeartbeat } from "../src/heartbeat.ts";
import { canIssue, type Capabilities } from "../src/capabilities.ts";

function allSupported(): Capabilities {
  return {
    pauseSupported: true,
    stopSupported: true,
    resumeSupported: true,
    checkpointMode: "SAFE_POINT",
    maxCheckpointDelayMs: 2000,
    adapterVersion: "0.1.0",
  };
}

test("all actions allowed when supported and heartbeat is fresh", () => {
  const caps = allSupported();
  const hb = emitHeartbeat(new ControlState(), null);
  const now = new Date(hb.emittedAt);

  assert.equal(canIssue("PAUSE", caps, hb, 30, now), true);
  assert.equal(canIssue("STOP", caps, hb, 30, now), true);
  assert.equal(canIssue("RESUME", caps, hb, 30, now), true);
});

test("unsupported capability blocks the action even with a fresh heartbeat", () => {
  const caps: Capabilities = { ...allSupported(), stopSupported: false };
  const hb = emitHeartbeat(new ControlState(), null);
  const now = new Date(hb.emittedAt);

  assert.equal(canIssue("STOP", caps, hb, 30, now), false);
});

test("stale heartbeat blocks the action even when supported", () => {
  const caps = allSupported();
  const hb = emitHeartbeat(new ControlState(), null);
  const longAfter = new Date(new Date(hb.emittedAt).getTime() + 120_000);

  assert.equal(canIssue("PAUSE", caps, hb, 30, longAfter), false);
});

test("unknown action is never allowed", () => {
  const caps = allSupported();
  const hb = emitHeartbeat(new ControlState(), null);
  const now = new Date(hb.emittedAt);

  assert.equal(canIssue("DELETE_EVERYTHING", caps, hb, 30, now), false);
});

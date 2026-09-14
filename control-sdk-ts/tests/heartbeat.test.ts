import { test } from "node:test";
import assert from "node:assert/strict";

import { ControlState, State } from "../src/controlState.ts";
import { effectiveState, emitHeartbeat } from "../src/heartbeat.ts";

test("fresh heartbeat reports the real state", () => {
  const cs = new ControlState();
  cs.requestPause();
  cs.confirmPaused();

  const hb = emitHeartbeat(cs, "run_abc");
  const now = new Date(hb.emittedAt);

  assert.equal(effectiveState(hb, 30, now), State.PAUSED);
});

test("stale heartbeat reports UNKNOWN, not the old state", () => {
  const cs = new ControlState(); // ACTIVE
  const hb = emitHeartbeat(cs, "run_abc");

  const longAfter = new Date(new Date(hb.emittedAt).getTime() + 120_000);

  assert.equal(effectiveState(hb, 30, longAfter), State.UNKNOWN);
});

test("missing heartbeat reports UNKNOWN", () => {
  assert.equal(effectiveState(null, 30), State.UNKNOWN);
});

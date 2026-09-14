import { test } from "node:test";
import assert from "node:assert/strict";

import { ControlState, IllegalTransition, State } from "../src/controlState.ts";

test("starts ACTIVE with version zero", () => {
  const cs = new ControlState();
  assert.equal(cs.state, State.ACTIVE);
  assert.equal(cs.stateVersion, 0);
});

test("full pause then resume cycle", () => {
  const cs = new ControlState();

  cs.requestPause();
  assert.equal(cs.state, State.PAUSE_REQUESTED);

  cs.confirmPaused();
  assert.equal(cs.state, State.PAUSED);

  cs.requestResume();
  assert.equal(cs.state, State.RESUME_REQUESTED);

  cs.confirmResumed();
  assert.equal(cs.state, State.ACTIVE);
  assert.equal(cs.stateVersion, 4);
});

test("full stop then resume cycle re-enables future work", () => {
  const cs = new ControlState();

  cs.requestStop();
  cs.confirmStopped();
  assert.equal(cs.state, State.STOPPED);

  cs.requestResume();
  cs.confirmResumed();
  assert.equal(cs.state, State.ACTIVE);
});

test("stop can interrupt a pause in progress", () => {
  const cs = new ControlState();
  cs.requestPause();
  cs.requestStop();
  assert.equal(cs.state, State.STOP_REQUESTED);
});

test("illegal transition is rejected, not guessed", () => {
  const cs = new ControlState();

  assert.throws(() => cs.confirmPaused(), IllegalTransition);

  // rejecting the illegal call must not have mutated state
  assert.equal(cs.state, State.ACTIVE);
  assert.equal(cs.stateVersion, 0);
});

test("cannot pause while already stopped", () => {
  const cs = new ControlState();
  cs.requestStop();
  cs.confirmStopped();

  assert.throws(() => cs.requestPause(), IllegalTransition);
});

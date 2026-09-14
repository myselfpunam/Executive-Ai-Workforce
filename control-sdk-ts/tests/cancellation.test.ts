import { test } from "node:test";
import assert from "node:assert/strict";

import { ControlState } from "../src/controlState.ts";
import { CancellationToken } from "../src/cancellation.ts";

test("token reflects a stop request", () => {
  const cs = new ControlState();
  const token = new CancellationToken(cs);

  assert.equal(token.isCancelled, false);

  cs.requestStop();
  assert.equal(token.isCancelled, true);
});

test("checking the token never mutates control state", () => {
  const cs = new ControlState();
  cs.requestStop();
  const token = new CancellationToken(cs);

  const versionBefore = cs.stateVersion;
  for (let i = 0; i < 5; i++) {
    void token.isCancelled;
  }

  assert.equal(cs.stateVersion, versionBefore);
  assert.equal(cs.isStopRequested(), true);
});

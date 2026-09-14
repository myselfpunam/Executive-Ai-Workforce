import { test } from "node:test";
import assert from "node:assert/strict";

import { ControlState } from "../src/controlState.ts";
import { CommandInbox, type CommandResult } from "../src/commandInbox.ts";

test("same command id delivered twice only takes effect once", () => {
  const cs = new ControlState();
  const inbox = new CommandInbox();
  let applyCount = 0;

  const applyPause = (): CommandResult => {
    applyCount += 1;
    cs.requestPause();
    cs.confirmPaused();
    return {
      commandId: "cmd_1",
      status: "APPLIED",
      resultingState: cs.state,
      stateVersion: cs.stateVersion,
    };
  };

  const first = inbox.handle("cmd_1", applyPause);
  const second = inbox.handle("cmd_1", applyPause); // simulated retry

  assert.equal(applyCount, 1);
  assert.deepEqual(first, second);
  assert.equal(cs.stateVersion, 2); // not 4 — no double transition
});

test("different command ids are each applied once", () => {
  const cs = new ControlState();
  const inbox = new CommandInbox();

  const applyPause = (): CommandResult => {
    cs.requestPause();
    cs.confirmPaused();
    return { commandId: "cmd_a", status: "APPLIED", resultingState: cs.state, stateVersion: cs.stateVersion };
  };
  const applyResume = (): CommandResult => {
    cs.requestResume();
    cs.confirmResumed();
    return { commandId: "cmd_b", status: "APPLIED", resultingState: cs.state, stateVersion: cs.stateVersion };
  };

  inbox.handle("cmd_a", applyPause);
  inbox.handle("cmd_b", applyResume);

  assert.equal(cs.state, "ACTIVE");
  assert.equal(cs.stateVersion, 4);
});

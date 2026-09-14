import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { ControlState } from "../src/controlState.ts";
import { loadCheckpoint, saveCheckpoint } from "../src/checkpoint.ts";

test("save then load round-trips the right fields", () => {
  const dir = mkdtempSync(join(tmpdir(), "checkpoint-"));
  try {
    const cs = new ControlState();
    cs.requestPause();
    cs.confirmPaused();

    const path = join(dir, "run.checkpoint.json");
    saveCheckpoint("run_123", 2, cs, path);

    const saved = loadCheckpoint(path);
    assert.deepEqual(saved, {
      runId: "run_123",
      nextStepIndex: 2,
      controlState: "PAUSED",
      stateVersion: cs.stateVersion,
    });
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
});

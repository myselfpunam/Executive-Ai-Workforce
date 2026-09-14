# control-sdk-ts

**Plane:** Control (agent-side adapter).

**Role:** the TypeScript equivalent of `control-sdk-python/`, for agent runtimes written in TypeScript/Node. Same contract: checkpoints, cancel token, heartbeat, capability advertisement, idempotent command inbox.

**Status:** fully ported from `control-sdk-python/` — state machine, heartbeat, capabilities, command inbox, checkpoint, cancellation token. 18/18 tests passing (Node's built-in test runner, `npm test`; type-check with `npm run typecheck`). No extra dependencies beyond `typescript` — Node runs `.ts` files natively.

**Depends on:** `control-sdk-python/`'s design (built first, so both SDKs implement the same contract rather than drifting independently).

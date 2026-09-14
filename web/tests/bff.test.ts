import { test } from "node:test";
import assert from "node:assert/strict";
import { createServer } from "node:http";

import { createBffServer } from "../src/bff.ts";
import { listenEphemeral } from "./testServer.ts";

function jsonStubServer(statusCode: number, body: unknown) {
  return createServer((_req, res) => {
    res.writeHead(statusCode, { "content-type": "application/json" });
    res.end(JSON.stringify(body));
  });
}

test("GET /bff/runs/:traceId proxies the Observation API's response", async () => {
  const observationStub = jsonStubServer(200, { run_id: "run_abc", status: "COMPLETED" });
  const observation = await listenEphemeral(observationStub);
  const bffServer = createBffServer({
    controlApiBaseUrl: "http://localhost:1", // unused in this test
    observationApiBaseUrl: `http://localhost:${observation.port}`,
  });
  const bff = await listenEphemeral(bffServer);

  try {
    const response = await fetch(`http://localhost:${bff.port}/bff/runs/trace123`);
    const body = (await response.json()) as { run_id: string; status: string };

    assert.equal(response.status, 200);
    assert.equal(body.run_id, "run_abc");
    assert.equal(body.status, "COMPLETED");
  } finally {
    await bff.close();
    await observation.close();
  }
});

test("GET /bff/runs/:traceId relays a 404 from the Observation API unchanged", async () => {
  const observationStub = jsonStubServer(404, { code: "UNKNOWN_TRACE", message: "no such run" });
  const observation = await listenEphemeral(observationStub);
  const bffServer = createBffServer({
    controlApiBaseUrl: "http://localhost:1",
    observationApiBaseUrl: `http://localhost:${observation.port}`,
  });
  const bff = await listenEphemeral(bffServer);

  try {
    const response = await fetch(`http://localhost:${bff.port}/bff/runs/does-not-exist`);
    assert.equal(response.status, 404);
  } finally {
    await bff.close();
    await observation.close();
  }
});

test("POST /bff/agents/:agentId/commands proxies to the Control API with the same body", async () => {
  let receivedBody = "";
  let receivedPath = "";
  const controlStub = createServer(async (req, res) => {
    receivedPath = req.url ?? "";
    const chunks: Buffer[] = [];
    for await (const chunk of req) chunks.push(chunk as Buffer);
    receivedBody = Buffer.concat(chunks).toString("utf-8");
    res.writeHead(202, { "content-type": "application/json" });
    res.end(JSON.stringify({ command_id: "cmd_xyz", status: "QUEUED" }));
  });
  const control = await listenEphemeral(controlStub);
  const bffServer = createBffServer({
    controlApiBaseUrl: `http://localhost:${control.port}`,
    observationApiBaseUrl: "http://localhost:1",
  });
  const bff = await listenEphemeral(bffServer);

  try {
    const requestBody = { action: "PAUSE", expected_state_version: 0, reason: "test" };
    const response = await fetch(`http://localhost:${bff.port}/bff/agents/agent_1/commands`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(requestBody),
    });
    const body = (await response.json()) as { command_id: string; status: string };

    assert.equal(response.status, 202);
    assert.equal(body.command_id, "cmd_xyz");
    assert.equal(receivedPath, "/control/v1/agents/agent_1/commands");
    assert.deepEqual(JSON.parse(receivedBody), requestBody);
  } finally {
    await bff.close();
    await control.close();
  }
});

test("an unknown route returns 404 from the BFF itself", async () => {
  const bffServer = createBffServer({ controlApiBaseUrl: "http://localhost:1", observationApiBaseUrl: "http://localhost:1" });
  const bff = await listenEphemeral(bffServer);

  try {
    const response = await fetch(`http://localhost:${bff.port}/bff/nonsense`);
    assert.equal(response.status, 404);
  } finally {
    await bff.close();
  }
});

test("an unreachable upstream results in a 502, never a silent empty success", async () => {
  const bffServer = createBffServer({
    controlApiBaseUrl: "http://localhost:1",
    observationApiBaseUrl: "http://localhost:1", // nothing listens here
  });
  const bff = await listenEphemeral(bffServer);

  try {
    const response = await fetch(`http://localhost:${bff.port}/bff/runs/whatever`);
    assert.equal(response.status, 502);
    const body = (await response.json()) as { code: string };
    assert.equal(body.code, "UPSTREAM_UNAVAILABLE");
  } finally {
    await bff.close();
  }
});

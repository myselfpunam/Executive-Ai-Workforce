import { createServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";

// No extra HTTP framework — Node's built-in http server + fetch are
// enough for a handful of routes (same "native tools are often enough"
// lesson as control-sdk-ts). Zero runtime dependencies.

export interface BffConfig {
  controlApiBaseUrl: string;
  observationApiBaseUrl: string;
}

async function readBody(req: IncomingMessage): Promise<string> {
  const chunks: Buffer[] = [];
  for await (const chunk of req) {
    chunks.push(chunk as Buffer);
  }
  return Buffer.concat(chunks).toString("utf-8");
}

function sendJson(res: ServerResponse, statusCode: number, body: unknown): void {
  const payload = JSON.stringify(body);
  res.writeHead(statusCode, { "content-type": "application/json" });
  res.end(payload);
}

/**
 * The BFF: the ONLY thing a browser ever talks to. It never stores
 * anything of its own — every route just forwards to Control API or
 * Observation API and relays the response. CLAUDE.md: "Only the BFF
 * joins read models for display" — Control and Observation stay separate
 * services; this is where their outputs are allowed to sit side by side.
 */
export function createBffServer(config: BffConfig): Server {
  return createServer(async (req, res) => {
    try {
      const url = new URL(req.url ?? "/", "http://localhost");

      if (req.method === "GET" && url.pathname === "/bff/health") {
        sendJson(res, 200, { status: "ok" });
        return;
      }

      const runMatch = url.pathname.match(/^\/bff\/runs\/([^/]+)$/);
      if (req.method === "GET" && runMatch) {
        const traceId = runMatch[1];
        const upstream = await fetch(`${config.observationApiBaseUrl}/observation/v1/runs/${traceId}`);
        const body = await upstream.json();
        sendJson(res, upstream.status, body);
        return;
      }

      const commandMatch = url.pathname.match(/^\/bff\/agents\/([^/]+)\/commands$/);
      if (req.method === "POST" && commandMatch) {
        const agentId = commandMatch[1];
        const requestBody = await readBody(req);
        const upstream = await fetch(`${config.controlApiBaseUrl}/control/v1/agents/${agentId}/commands`, {
          method: "POST",
          headers: { "content-type": "application/json" },
          body: requestBody,
        });
        const body = await upstream.json();
        sendJson(res, upstream.status, body);
        return;
      }

      sendJson(res, 404, { code: "NOT_FOUND", message: `no such route: ${req.method} ${url.pathname}` });
    } catch (error) {
      // The upstream (Control API or Observation API) was unreachable —
      // never silently return an empty success, say honestly that the
      // join failed.
      sendJson(res, 502, { code: "UPSTREAM_UNAVAILABLE", message: (error as Error).message });
    }
  });
}

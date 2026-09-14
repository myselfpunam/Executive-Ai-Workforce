import type { Server } from "node:http";

export interface RunningServer {
  port: number;
  close: () => Promise<void>;
}

/** Starts `server` on an OS-assigned free port. Used both for the BFF
 * itself and for small stand-in servers that play the role of Control
 * API / Observation API in these tests — genuine HTTP over loopback, not
 * a mocked fetch, just a smaller server we fully control. */
export function listenEphemeral(server: Server): Promise<RunningServer> {
  return new Promise((resolve) => {
    server.listen(0, () => {
      const address = server.address();
      const port = typeof address === "object" && address !== null ? address.port : 0;
      resolve({
        port,
        close: () => new Promise((res) => server.close(() => res())),
      });
    });
  });
}

import { createBffServer } from "./bff.ts";

const port = Number(process.env.PORT ?? 8080);
const controlApiBaseUrl = process.env.CONTROL_API_URL ?? "http://localhost:8000";
const observationApiBaseUrl = process.env.OBSERVATION_API_URL ?? "http://localhost:8001";

const server = createBffServer({ controlApiBaseUrl, observationApiBaseUrl });
server.listen(port, () => {
  console.log(`BFF + dashboard listening on http://localhost:${port}`);
  console.log(`  -> Control API:     ${controlApiBaseUrl}`);
  console.log(`  -> Observation API: ${observationApiBaseUrl}`);
});

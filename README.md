# Executive AI Workforce Control Room + Twenty CRM

Read-only AI-agent observation, a minimal PAUSE/STOP/RESUME control plane, and a read-only Twenty CRM connector — built by KeyPillar AI LTD as a self-hosted, licensed product.

Start here: [START_HERE.md](START_HERE.md)

Project rules and architecture: [CLAUDE.md](CLAUDE.md), [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md)

Plan and progress: [WEEKLY_ROADMAP.md](WEEKLY_ROADMAP.md), [CHECKLIST.md](CHECKLIST.md)

## Layout

| Folder | Plane | Language | Status |
|---|---|---|---|
| `agent-runtime/` | AI/Business (demo agent) | Python | In progress |
| `control-sdk-python/` | Control | Python | Not started |
| `control-sdk-ts/` | Control | TypeScript | Not started |
| `control-api/` | Control | TBD | Not started |
| `observation/` | Observation | TBD | Not started |
| `twenty-connector/` | Twenty (business truth) | TBD | Not started |
| `web/` | Executive UI | TypeScript | Not started |
| `vendor-distribution/` | Vendor Distribution (Phase 2) | TBD | Not started |
| `docs/` | Reference material | — | — |

A single Python virtual environment at the repo root (`venv/`, gitignored) is shared across all Python folders for now — no per-folder venvs until there's a real reason to isolate dependencies.

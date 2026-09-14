from __future__ import annotations

import os

import psycopg
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from control_sdk.command_schema import validate_command_request

from .commands import submit_command as submit_command_transaction
from .policy import StaleStateVersion

app = FastAPI(title="Control API")


@app.post("/control/v1/agents/{agent_id}/commands", status_code=202)
async def submit_command(agent_id: str, request: Request) -> JSONResponse:
    """The only write endpoint (CLAUDE.md section 11). We parse the raw
    body ourselves — not a Pydantic model — so validate_command_request
    (the SAME function the SDKs use) is the single source of truth for
    "reject unknown fields," not a second, possibly-different check."""
    try:
        body = await request.json()
    except Exception:
        body = None

    if not isinstance(body, dict):
        return JSONResponse(status_code=400, content={"code": "SCHEMA_VALIDATION_FAILED", "message": "body must be a JSON object"})

    error = validate_command_request(body)
    if error is not None:
        return JSONResponse(status_code=400, content={"code": error.code, "message": error.message})

    conn = psycopg.connect(os.environ["DATABASE_URL"])
    try:
        try:
            command_id = submit_command_transaction(
                conn,
                agent_id=agent_id,
                action=body["action"],
                expected_state_version=body["expected_state_version"],
                reason=body["reason"],
            )
        except StaleStateVersion as exc:
            return JSONResponse(
                status_code=409,
                content={
                    "code": "STALE_STATE_VERSION",
                    "message": str(exc),
                    "current_state_version": exc.actual,
                },
            )
    finally:
        conn.close()

    return JSONResponse(status_code=202, content={"command_id": command_id, "status": "QUEUED"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

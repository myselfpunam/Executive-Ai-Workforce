from __future__ import annotations

import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .webhook import InvalidWebhookSignature, verify_webhook_signature

app = FastAPI(title="Twenty Webhook Receiver")


@app.post("/twenty/webhook")
async def receive_webhook(request: Request) -> JSONResponse:
    raw_body = (await request.body()).decode("utf-8")
    timestamp = request.headers.get("x-twenty-webhook-timestamp", "")
    signature = request.headers.get("x-twenty-webhook-signature", "")

    try:
        verify_webhook_signature(
            secret=os.environ["TWENTY_WEBHOOK_SECRET"],
            timestamp=timestamp,
            raw_body=raw_body,
            provided_signature=signature,
        )
    except InvalidWebhookSignature as exc:
        return JSONResponse(status_code=401, content={"code": "INVALID_WEBHOOK_SIGNATURE", "message": str(exc)})

    # For now: just acknowledge quickly (2xx, per Twenty's requirement).
    # Step 40 (reconciliation poller) is what actually reconciles Twenty
    # state into anything we act on — this receiver's only job is to
    # accept genuine, verified notifications fast.
    return JSONResponse(status_code=200, content={"status": "received"})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)

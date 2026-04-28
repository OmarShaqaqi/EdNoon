from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException, status

from .config import WebhookConfig
from .schemas import InterventionLogIn, InterventionLogRecord
from .storage import append_intervention_log, count_log_rows


config = WebhookConfig()
app = FastAPI(
    title="Boon Intervention Webhook API",
    description="Receives intervention feedback events from Zapier.",
    version="0.1.0",
)


def verify_webhook_key(x_webhook_key: str | None = Header(default=None)) -> None:
    """Protect the endpoint when WEBHOOK_API_KEY is configured."""
    if not config.api_key:
        return
    if x_webhook_key != config.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing webhook key.",
        )


@app.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "log_path": str(config.log_path),
        "stored_events": count_log_rows(config.log_path),
    }


@app.post("/intervention-log", status_code=status.HTTP_201_CREATED)
def receive_intervention_log(
    payload: InterventionLogIn,
    _: None = Depends(verify_webhook_key),
) -> dict[str, object]:
    """Receive one facilitator feedback event from Zapier and store it as CSV."""
    record = InterventionLogRecord.from_payload(payload)
    append_intervention_log(record, config.log_path)
    return {
        "saved": True,
        "student_id": record.student_id,
        "status": record.status,
        "stored_events": count_log_rows(config.log_path),
    }

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


InterventionStatus = Literal[
    "started",
    "message_sent",
    "called_parent",
    "no_answer",
    "parent_replied",
    "tutoring_scheduled",
    "resolved",
    "escalated",
    "wrong_number",
]

ContactMethod = Literal[
    "whatsapp",
    "phone_call",
    "in_person",
    "tutoring",
    "campus_lead",
    "other",
]


class InterventionLogIn(BaseModel):
    """Payload Zapier sends after a facilitator submits the feedback form."""

    model_config = ConfigDict(str_strip_whitespace=True)

    student_id: str = Field(..., min_length=1)
    student_name: str = Field(..., min_length=1)
    facilitator_email: str = Field(..., min_length=3)
    risk_score: float = Field(0.0, ge=0, le=100)
    recommended_action: str = Field(..., min_length=1)
    status: InterventionStatus = "started"
    contact_method: ContactMethod = "other"
    outcome_notes: str = ""

    @field_validator("student_id")
    @classmethod
    def normalize_student_id(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("facilitator_email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return value.strip().lower()

    @field_validator("risk_score", mode="before")
    @classmethod
    def parse_zapier_risk_score(cls, value: object) -> float:
        """Accept Zapier/Form values like '73.1', '73.1%', or an empty field."""
        if isinstance(value, (int, float)):
            return float(value)
        if value is None:
            return 0.0

        text = str(value).strip()
        match = re.search(r"-?\d+(?:\.\d+)?", text)
        if not match:
            return 0.0
        return float(match.group(0))


class InterventionLogRecord(InterventionLogIn):
    """Persisted intervention log row with server-side metadata."""

    timestamp: str
    source: str = "zapier_webhook"

    @classmethod
    def from_payload(cls, payload: InterventionLogIn) -> "InterventionLogRecord":
        return cls(
            **payload.model_dump(),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

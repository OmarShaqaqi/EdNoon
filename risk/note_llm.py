from __future__ import annotations

import json
import os
from dataclasses import dataclass

import pandas as pd

from .config import RiskConfig


NOTE_RISK_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "risk": {"type": "number", "minimum": 0, "maximum": 10},
        "confidence": {"type": "number", "minimum": 0, "maximum": 10},
        "reason": {"type": "string"},
        "signals": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "attendance_issue",
                    "practice_issue",
                    "parent_unresponsive",
                    "academic_struggle",
                    "emotional_or_family_issue",
                    "positive_momentum",
                    "possible_data_quality_issue",
                    "other",
                ],
            },
        },
    },
    "required": ["risk", "confidence", "reason", "signals"],
}


@dataclass
class NoteRiskResult:
    risk: float | None
    available: bool
    confidence: float
    reason: str
    source: str
    signals: str


class NoteRiskAnalyzer:
    def __init__(self, config: RiskConfig) -> None:
        self.model = os.getenv("OPENAI_MODEL", config.note_model)
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = self._build_client() if self.api_key else None

    def analyze_row(self, row: pd.Series) -> NoteRiskResult:
        notes_history = str(row.get("notes_history", "") or "").strip()
        if not notes_history:
            return NoteRiskResult(
                risk=None,
                available=False,
                confidence=0.0,
                reason="No facilitator notes available.",
                source="none",
                signals="",
            )
        if not self.api_key:
            return NoteRiskResult(
                risk=None,
                available=False,
                confidence=0.0,
                reason="OPENAI_API_KEY not configured; note risk skipped.",
                source="missing_api_key",
                signals="",
            )
        if self.client is None:
            return NoteRiskResult(
                risk=None,
                available=False,
                confidence=0.0,
                reason="openai package is not installed; note risk skipped.",
                source="missing_openai_package",
                signals="",
            )

        try:
            parsed = self._call_openai(row, notes_history)
            return NoteRiskResult(
                risk=clip01(float(parsed["risk"]) / 10),
                available=True,
                confidence=clip01(float(parsed["confidence"]) / 10),
                reason=str(parsed["reason"]),
                source="openai",
                signals=",".join(parsed.get("signals", [])),
            )
        except Exception as exc:
            return NoteRiskResult(
                risk=None,
                available=False,
                confidence=0.0,
                reason=f"LLM note analysis failed: {exc}",
                source="llm_error",
                signals="",
            )

    def _build_client(self):
        try:
            from openai import OpenAI
        except ImportError:
            return None
        return OpenAI(api_key=self.api_key)

    def _call_openai(self, row: pd.Series, notes_history: str) -> dict:
        response = self.client.responses.create(
            model=self.model,
            instructions=(
                "You are analyzing facilitator notes for a Saudi test-prep intervention system. "
                "Return JSON only. Score risk from 0 to 10 based only on the notes, where 0 means "
                "the notes show no concern or positive momentum, and 10 means urgent intervention is needed. "
                "Score confidence from 0 to 10, where 10 means the notes clearly support the assessment. "
                "Consider attendance concerns, practice refusal, parent non-response, academic struggle, "
                "emotional/family issues, and possible data-quality/name mismatches. Be concise."
            ),
            input=(
                f"Student: {row.get('student_name', '')} ({row.get('student_id', '')})\n"
                f"Campus: {row.get('campus_id', '')}\n"
                f"Latest quiz score: {row.get('latest_quiz_score', '')}\n"
                f"Recent attendance rate: {row.get('recent_attendance_rate', '')}\n"
                f"Recent practice avg/day: {row.get('recent_practice_questions_avg', '')}\n\n"
                f"Facilitator notes timeline:\n{notes_history}"
            ),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "note_risk",
                    "schema": NOTE_RISK_SCHEMA,
                    "strict": True,
                }
            },
            temperature=0,
        )
        return json.loads(response.output_text)


def clip01(value: float) -> float:
    return max(0.0, min(1.0, value))

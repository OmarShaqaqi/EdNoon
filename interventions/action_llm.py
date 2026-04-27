from __future__ import annotations

import json
import os
from dataclasses import dataclass

import pandas as pd

from .config import InterventionConfig


ACTION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "recommended_action": {"type": "string"},
        "message_draft": {"type": "string"},
        "needs_human_review": {"type": "boolean"},
        "review_reason": {"type": "string"},
    },
    "required": ["recommended_action", "message_draft", "needs_human_review", "review_reason"],
}


@dataclass
class ActionPlanResult:
    recommended_action: str
    message_draft: str
    needs_human_review: bool
    review_reason: str
    source: str


class ActionPlannerLLM:
    def __init__(self, config: InterventionConfig) -> None:
        self.config = config
        self.model = os.getenv("OPENAI_MODEL", config.action_model)
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = self._build_client() if self.api_key else None

    def plan_row(self, row: pd.Series) -> ActionPlanResult:
        if not self.api_key:
            return fallback_action_plan(row, self.config, "missing_api_key")
        if self.client is None:
            return fallback_action_plan(row, self.config, "missing_openai_package")
        try:
            parsed = self._call_openai(row)
            return ActionPlanResult(
                recommended_action=str(parsed["recommended_action"]),
                message_draft=str(parsed["message_draft"]),
                needs_human_review=bool(parsed["needs_human_review"]),
                review_reason=str(parsed["review_reason"]),
                source="openai",
            )
        except Exception as exc:
            fallback = fallback_action_plan(row, self.config, "llm_error")
            return ActionPlanResult(
                recommended_action=fallback.recommended_action,
                message_draft=fallback.message_draft,
                needs_human_review=True,
                review_reason=f"LLM action planning failed: {exc}",
                source="llm_error",
            )

    def _build_client(self):
        try:
            from openai import OpenAI
        except ImportError:
            return None
        return OpenAI(api_key=self.api_key)

    def _call_openai(self, row: pd.Series) -> dict:
        response = self.client.responses.create(
            model=self.model,
            instructions=(
                "You are helping a Saudi test-prep facilitator choose one practical intervention. "
                "Return JSON only. Recommend a concrete next action and draft a short Arabic WhatsApp "
                "message to the parent. Be respectful, specific, and avoid blaming the student or parent. "
                "The message_draft field must be fully in Arabic. "
                "If phone/contact data looks invalid or the notes suggest a possible student mismatch, "
                "set needs_human_review=true and explain why. Do not invent facts."
            ),
            input=build_prompt(row, self.config),
            text={
                "format": {
                    "type": "json_schema",
                    "name": "intervention_action",
                    "schema": ACTION_SCHEMA,
                    "strict": True,
                }
            },
            temperature=0.2,
        )
        return json.loads(response.output_text)


def build_prompt(row: pd.Series, config: InterventionConfig) -> str:
    return (
        f"Student: {row.get('student_name', '')} ({row.get('student_id', '')})\n"
        f"Grade: {row.get('grade', '')}\n"
        f"Learning track: {row.get('learning_track', '')}\n"
        f"Campus: {row.get('campus_id', '')}\n"
        f"Facilitator: {row.get('facilitator_email', '')}\n"
        f"Parent phone: {row.get('parent_phone', '')}\n"
        f"Parent phone valid: {row.get('parent_phone_valid', '')}\n"
        f"Target score: {row.get('target_score', '')}\n"
        f"Latest quiz date: {row.get('latest_quiz_date', '')}\n"
        f"Latest quiz score: {row.get('latest_quiz_score', '')}\n"
        f"Previous quiz score: {row.get('previous_quiz_score', '')}\n"
        f"Quiz score delta: {row.get('quiz_score_delta', '')}\n"
        f"Failed latest quiz: {row.get('failed_latest_quiz', '')}\n"
        f"Target gap: {row.get('target_gap', '')}\n"
        f"Days until next quiz: {row.get('days_until_next_quiz', '')}\n"
        f"Recent days observed: {row.get('recent_days_observed', '')}\n"
        f"Recent sessions attended: {row.get('recent_sessions_attended', '')}\n"
        f"Recent zero-attendance days: {row.get('recent_zero_attendance_days', '')}\n"
        f"Recent attendance minutes average: {row.get('recent_attendance_min_avg', '')}\n"
        f"Recent attendance rate: {row.get('recent_attendance_rate', '')}\n"
        f"Recent practice questions average per day: {row.get('recent_practice_questions_avg', '')}\n"
        f"Recent practice questions total: {row.get('recent_practice_questions_total', '')}\n"
        f"Post-quiz days observed: {row.get('post_quiz_days_observed', '')}\n"
        f"Post-quiz sessions attended: {row.get('post_quiz_sessions_attended', '')}\n"
        f"Post-quiz zero-attendance days: {row.get('post_quiz_zero_attendance_days', '')}\n"
        f"Post-quiz attendance rate: {row.get('post_quiz_attendance_rate', '')}\n"
        f"Post-quiz practice questions total: {row.get('post_quiz_practice_questions_total', '')}\n"
        f"Risk score: {row.get('risk_score', '')} ({row.get('risk_level', '')})\n"
        f"Action priority: {row.get('action_priority', '')}\n"
        f"Risk reasons: {row.get('risk_reasons', '')}\n"
        f"Quiz score risk: {row.get('quiz_score_risk', '')}\n"
        f"Quiz trend risk: {row.get('quiz_trend_risk', '')}\n"
        f"Attendance risk: {row.get('attendance_risk', '')}\n"
        f"Practice risk: {row.get('practice_risk', '')}\n"
        f"Urgency risk: {row.get('urgency_risk', '')}\n"
        f"Notes count: {row.get('notes_count', '')}\n"
        f"Notes risk reason: {row.get('notes_risk_reason', '')}\n"
        f"Notes signals: {row.get('notes_risk_signals', '')}\n"
        f"Latest note: {row.get('latest_note_text', '')}\n"
        f"Full notes timeline:\n{row.get('notes_history', '')}\n"
        f"Next quiz label: {config.quiz_day_label}\n"
    )


def fallback_action_plan(row: pd.Series, config: InterventionConfig, source: str) -> ActionPlanResult:
    action = fallback_recommended_action(row)
    message = fallback_message_draft(row, config)
    review_reasons = fallback_review_reasons(row)
    return ActionPlanResult(
        recommended_action=action,
        message_draft=message,
        needs_human_review=bool(review_reasons),
        review_reason="; ".join(review_reasons),
        source=source,
    )


def fallback_recommended_action(row: pd.Series) -> str:
    signals = str(row.get("notes_risk_signals", "") or "")
    if "parent_unresponsive" in signals:
        return "Escalate parent contact: call, WhatsApp, then campus lead if no response"
    if row.get("attendance_risk", 0) >= 0.55:
        return "Call parent today to diagnose attendance barrier"
    if row.get("practice_risk", 0) >= 0.65:
        return "Send practice accountability message and assign a small daily target"
    if row.get("quiz_score_risk_available") and row.get("quiz_score_risk", 0) >= 0.4:
        return "Schedule short 1:1 academic support before next quiz"
    if row.get("notes_risk_available") and row.get("notes_risk", 0) >= 0.5:
        return "Facilitator check-in based on note concern"
    return "Send motivational nudge and monitor tomorrow"


def fallback_message_draft(row: pd.Series, config: InterventionConfig) -> str:
    first_name = str(row.get("student_name", "")).split()[0]
    reasons = arabic_reason_summary(row)
    if row["action_priority"] == "today":
        return (
            f"السلام عليكم، معكم فريق بون. نحتاج نساعد {first_name} قبل {config.quiz_day_label}. "
            f"لاحظنا: {reasons}. هل يناسبكم اتصال قصير اليوم لوضع خطة دعم؟"
        )
    if row["action_priority"] == "within_48h":
        return (
            f"السلام عليكم، نود دعم {first_name} قبل {config.quiz_day_label}. "
            f"الملاحظة الحالية: {reasons}. نرجو متابعة تدريب اليوم وسنتواصل معكم عند الحاجة."
        )
    return (
        f"السلام عليكم، نرسل تذكير بسيط لـ {first_name} بالمحافظة على الحضور والتدريب اليومي "
        f"قبل {config.quiz_day_label}."
    )


def arabic_reason_summary(row: pd.Series) -> str:
    reasons: list[str] = []
    if bool(row.get("quiz_score_risk_available", False)) and pd.notna(row.get("latest_quiz_score")):
        latest_score = float(row.get("latest_quiz_score"))
        if latest_score < 70:
            reasons.append(f"درجة الاختبار الأخيرة {latest_score:.0f}")
    if pd.notna(row.get("recent_attendance_rate")) and float(row.get("recent_attendance_rate")) < 0.7:
        reasons.append(f"نسبة الحضور الأخيرة {float(row.get('recent_attendance_rate')):.0%}")
    if pd.notna(row.get("recent_practice_questions_avg")) and float(row.get("recent_practice_questions_avg")) < 10:
        reasons.append(f"متوسط التدريب اليومي {float(row.get('recent_practice_questions_avg')):.1f} سؤال")
    if str(row.get("notes_risk_signals", "") or ""):
        reasons.append("توجد ملاحظات من الميسر تحتاج متابعة")
    return "، و".join(reasons) if reasons else "نحتاج متابعة بسيطة قبل الاختبار"


def fallback_review_reasons(row: pd.Series) -> list[str]:
    reasons: list[str] = []
    if not bool(row.get("parent_phone_valid", False)):
        reasons.append("invalid parent phone")
    if row.get("notes_risk_source") == "llm_error":
        reasons.append("LLM note analysis failed")
    signals = str(row.get("notes_risk_signals", "") or "")
    if "possible_data_quality_issue" in signals:
        reasons.append("possible note/student mismatch")
    return reasons

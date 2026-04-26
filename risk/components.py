from __future__ import annotations

import pandas as pd

from .config import RiskConfig
from .note_llm import NoteRiskAnalyzer


def add_risk_components(
    features: pd.DataFrame, config: RiskConfig, note_analyzer: NoteRiskAnalyzer | None = None
) -> pd.DataFrame:
    scored = features.copy()
    note_analyzer = note_analyzer or NoteRiskAnalyzer(config)

    scored["quiz_score_risk_available"] = scored["has_quiz"].astype(bool)
    scored["quiz_score_risk"] = 1 - (scored["latest_quiz_score"] / 100)
    scored.loc[~scored["quiz_score_risk_available"], "quiz_score_risk"] = pd.NA

    scored["quiz_trend_risk_available"] = scored["quiz_count"].ge(2) & scored["quiz_score_delta"].notna()
    scored["quiz_trend_risk"] = ((10 - scored["quiz_score_delta"]) / 40).clip(0, 1)
    scored.loc[~scored["quiz_trend_risk_available"], "quiz_trend_risk"] = pd.NA

    scored["attendance_risk_available"] = scored["recent_days_observed"].gt(0)
    scored["attendance_risk"] = (1 - scored["recent_attendance_rate"]).clip(0, 1)
    scored.loc[~scored["attendance_risk_available"], "attendance_risk"] = pd.NA

    scored["practice_risk_available"] = scored["recent_days_observed"].gt(0)
    scored["practice_risk"] = (
        1 - (scored["recent_practice_questions_avg"] / config.expected_practice_questions_per_day)
    ).clip(0, 1)
    scored.loc[~scored["practice_risk_available"], "practice_risk"] = pd.NA

    note_results = scored.apply(note_analyzer.analyze_row, axis=1)
    scored["notes_risk"] = note_results.map(lambda result: result.risk)
    scored["notes_risk_available"] = note_results.map(lambda result: result.available)
    scored["notes_risk_confidence"] = note_results.map(lambda result: result.confidence)
    scored["notes_risk_reason"] = note_results.map(lambda result: result.reason)
    scored["notes_risk_source"] = note_results.map(lambda result: result.source)
    scored["notes_risk_signals"] = note_results.map(lambda result: result.signals)
    scored.loc[~scored["notes_risk_available"], "notes_risk"] = pd.NA

    scored["urgency_risk_available"] = scored["days_until_next_quiz"].lt(999)
    scored["urgency_risk"] = (
        (config.urgent_days_until_quiz - scored["days_until_next_quiz"]) / config.urgent_days_until_quiz
    ).clip(0, 1)
    scored.loc[~scored["urgency_risk_available"], "urgency_risk"] = pd.NA

    return scored

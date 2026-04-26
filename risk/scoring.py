from __future__ import annotations

import pandas as pd

from .config import RiskConfig


COMPONENTS = [
    ("quiz_score_risk", "quiz_score_weight"),
    ("quiz_trend_risk", "quiz_trend_weight"),
    ("attendance_risk", "attendance_weight"),
    ("practice_risk", "practice_weight"),
    ("notes_risk", "notes_weight"),
    ("urgency_risk", "urgency_weight"),
]


def add_final_risk_score(scored: pd.DataFrame, config: RiskConfig) -> pd.DataFrame:
    result = scored.copy()
    weighted_sum = pd.Series(0.0, index=result.index)
    available_weight = pd.Series(0.0, index=result.index)

    for risk_column, weight_attribute in COMPONENTS:
        available_column = f"{risk_column}_available"
        weight = getattr(config, weight_attribute)
        available = result[available_column].astype(bool)
        risk_values = pd.to_numeric(result[risk_column], errors="coerce").fillna(0)
        weighted_sum += risk_values * weight * available.astype(float)
        available_weight += weight * available.astype(float)

    result["risk_available_weight"] = available_weight
    result["risk_score"] = 0.0
    has_available_components = available_weight.gt(0)
    result.loc[has_available_components, "risk_score"] = (
        weighted_sum[has_available_components] / available_weight[has_available_components] * 100
    ).round(1)
    result["risk_level"] = result["risk_score"].map(risk_level)
    result["risk_reasons"] = result.apply(risk_reasons, axis=1)
    return result.sort_values(["risk_score", "student_id"], ascending=[False, True])


def risk_level(score: float) -> str:
    if score >= 80:
        return "critical"
    if score >= 60:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def risk_reasons(row: pd.Series) -> str:
    reasons: list[str] = []
    if row.get("quiz_score_risk_available") and row.get("latest_quiz_score") < 70:
        reasons.append(f"latest quiz score {row['latest_quiz_score']:.0f}")
    if row.get("quiz_trend_risk_available") and row.get("quiz_score_delta") < 0:
        reasons.append(f"quiz score dropped {abs(row['quiz_score_delta']):.0f} pts")
    if row.get("attendance_risk_available") and row.get("attendance_risk", 0) >= 0.35:
        reasons.append(f"attendance rate {row['recent_attendance_rate']:.0%}")
    if row.get("practice_risk_available") and row.get("practice_risk", 0) >= 0.5:
        reasons.append(f"practice avg {row['recent_practice_questions_avg']:.1f}/day")
    if row.get("notes_risk_available") and row.get("notes_risk", 0) >= 0.45:
        reasons.append("facilitator notes show concern")
    if row.get("urgency_risk_available") and row.get("days_until_next_quiz") <= 3:
        reasons.append(f"{int(row['days_until_next_quiz'])} days until quiz")
    return "; ".join(reasons) if reasons else "no major risk signal"

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskConfig:
    note_model: str = "gpt-4o-mini"
    quiz_score_weight: float = 30
    quiz_trend_weight: float = 10
    attendance_weight: float = 25
    practice_weight: float = 20
    notes_weight: float = 10
    urgency_weight: float = 10
    expected_practice_questions_per_day: float = 20
    urgent_days_until_quiz: int = 7

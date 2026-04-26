from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureConfig:
    as_of_date: str = "2025-10-14"
    quiz_1_date: str = "2025-10-10"
    quiz_2_date: str = "2025-10-20"
    expected_session_minutes: int = 90
    recent_window_days: int = 7

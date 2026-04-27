from dataclasses import dataclass


@dataclass(frozen=True)
class InterventionConfig:
    action_model: str = "gpt-4o-mini"
    action_llm_concurrency: int = 80
    max_daily_actions_per_facilitator: int = 12
    critical_threshold: float = 80
    high_threshold: float = 60
    medium_threshold: float = 40
    quiz_day_label: str = "اختبار اللفظي"

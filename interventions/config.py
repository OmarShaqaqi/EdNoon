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
    update_form_url_template: str = (
        "https://docs.google.com/forms/d/e/1FAIpQLSczZrPRtoh2L4MxnhKv_h9KB_R9eC6R1Qgaze0h8QWGfTpt5g/viewform"
        "?usp=pp_url"
        "&entry.443725423={student_id}"
        "&entry.824519319={student_name}"
        "&entry.172396955={facilitator_email}"
        "&entry.2007502189={risk_score}"
        "&entry.1815215151={recommended_action}"
    )

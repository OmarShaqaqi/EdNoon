from dataclasses import dataclass


@dataclass(frozen=True)
class FeedbackConfig:
    acted_statuses: tuple[str, ...] = (
        "started",
        "message_sent",
        "called_parent",
        "no_answer",
        "parent_replied",
        "tutoring_scheduled",
        "resolved",
        "escalated",
        "wrong_number",
    )
    completed_statuses: tuple[str, ...] = (
        "message_sent",
        "called_parent",
        "parent_replied",
        "tutoring_scheduled",
        "resolved",
        "escalated",
    )
    followup_statuses: tuple[str, ...] = (
        "started",
        "no_answer",
        "wrong_number",
    )


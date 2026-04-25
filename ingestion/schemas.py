from dataclasses import dataclass


REQUIRED_COLUMNS = {
    "student_metadata": {
        "student_id",
        "student_name",
        "campus_id",
        "facilitator_email",
        "grade",
        "parent_phone",
        "target_score",
        "learning_track",
    },
    "student_daily_metrics": {
        "student_id",
        "date",
        "session_attended_min",
        "practice_questions",
        "last_quiz_score",
        "days_until_next_quiz",
    },
    "facilitator_notes": {
        "note_id",
        "student_id",
        "facilitator_email",
        "date",
        "note_text",
    },
}


@dataclass(frozen=True)
class SourceFiles:
    student_metadata: str = "student_metadata.csv"
    student_daily_metrics: str = "student_daily_metrics.csv"
    facilitator_notes: str = "facilitator_notes.csv"


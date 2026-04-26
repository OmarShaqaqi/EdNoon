from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import FeatureConfig


def build_student_features(input_dir: Path, output_dir: Path, config: FeatureConfig) -> pd.DataFrame:
    metadata, daily, notes = load_clean_inputs(input_dir)
    as_of = pd.Timestamp(config.as_of_date)
    quiz_1_date = pd.Timestamp(config.quiz_1_date)

    daily = daily[daily["date"] <= as_of].copy()
    notes = notes[notes["date"] <= as_of].copy()

    features = metadata.copy()
    features = features.merge(quiz_features(daily), on="student_id", how="left")
    features = features.merge(next_quiz_features(metadata, as_of, config), on="student_id", how="left")
    features = features.merge(recent_activity_features(daily, as_of, config), on="student_id", how="left")
    features = features.merge(post_quiz_activity_features(daily, quiz_1_date, as_of, config), on="student_id", how="left")
    features = features.merge(note_activity_features(notes, as_of), on="student_id", how="left")

    features = fill_feature_defaults(features)
    features["target_gap"] = 0.0
    has_quiz = features["has_quiz"]
    if has_quiz.any():
        features.loc[has_quiz, "target_gap"] = (
            features.loc[has_quiz, "target_score"] - features.loc[has_quiz, "latest_quiz_score"]
        ).clip(lower=0)
    features["failed_latest_quiz"] = has_quiz & features["latest_quiz_score"].lt(70)

    output_dir.mkdir(parents=True, exist_ok=True)
    features.to_csv(output_dir / f"student_features_{as_of.date()}.csv", index=False)
    return features


def load_clean_inputs(input_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    metadata = pd.read_csv(
        input_dir / "student_metadata_clean.csv",
        dtype={"student_id": str, "campus_id": str, "facilitator_email": str, "parent_phone": str},
    )
    daily = pd.read_csv(input_dir / "student_daily_metrics_clean.csv", dtype={"student_id": str})
    notes = pd.read_csv(
        input_dir / "facilitator_notes_clean.csv",
        dtype={"note_id": str, "student_id": str, "facilitator_email": str},
    )

    daily["date"] = pd.to_datetime(daily["date"], errors="coerce")
    notes["date"] = pd.to_datetime(notes["date"], errors="coerce")
    return metadata, daily, notes


def quiz_features(daily: pd.DataFrame) -> pd.DataFrame:
    quiz_rows = daily.dropna(subset=["last_quiz_score"]).sort_values(["student_id", "date"]).copy()
    if quiz_rows.empty:
        return pd.DataFrame(columns=["student_id"])

    # The daily table repeats last_quiz_score after a quiz. A quiz event is the
    # first available score for a student, or a later row where the score changes.
    previous_score = quiz_rows.groupby("student_id")["last_quiz_score"].shift()
    quiz_events = quiz_rows[previous_score.isna() | quiz_rows["last_quiz_score"].ne(previous_score)].copy()
    quiz_events["quiz_sequence"] = quiz_events.groupby("student_id").cumcount() + 1

    latest = quiz_events.groupby("student_id").tail(1).set_index("student_id")
    quiz_count = quiz_events.groupby("student_id").size().rename("quiz_count")
    latest_sequence = quiz_events.groupby("student_id")["quiz_sequence"].transform("max")
    previous = quiz_events[quiz_events["quiz_sequence"].eq(latest_sequence - 1)].set_index("student_id")

    features = latest[["date", "last_quiz_score", "quiz_sequence"]].rename(
        columns={
            "date": "latest_quiz_date",
            "last_quiz_score": "latest_quiz_score",
            "quiz_sequence": "latest_quiz_number",
        }
    )
    features = features.join(quiz_count)
    features = features.join(
        previous[["last_quiz_score"]].rename(columns={"last_quiz_score": "previous_quiz_score"})
    )
    features["quiz_score_delta"] = features["latest_quiz_score"] - features["previous_quiz_score"]
    features["has_quiz"] = True
    return features.reset_index()


def next_quiz_features(metadata: pd.DataFrame, as_of: pd.Timestamp, config: FeatureConfig) -> pd.DataFrame:
    quiz_dates = sorted([pd.Timestamp(config.quiz_1_date), pd.Timestamp(config.quiz_2_date)])
    future_quiz_dates = [quiz_date for quiz_date in quiz_dates if quiz_date > as_of]
    days_until_next_quiz = 999
    if future_quiz_dates:
        days_until_next_quiz = int((future_quiz_dates[0] - as_of).days)

    return pd.DataFrame(
        {
            "student_id": metadata["student_id"],
            "days_until_next_quiz": days_until_next_quiz,
        }
    )


def recent_activity_features(
    daily: pd.DataFrame, as_of: pd.Timestamp, config: FeatureConfig
) -> pd.DataFrame:
    start_date = as_of - pd.Timedelta(days=config.recent_window_days - 1)
    recent = daily[daily["date"].between(start_date, as_of)].copy()

    grouped = recent.groupby("student_id").agg(
        recent_days_observed=("date", "nunique"),
        recent_sessions_attended=("session_attended_min", lambda s: int((s > 0).sum())),
        recent_attendance_min_avg=("session_attended_min", "mean"),
        recent_practice_questions_avg=("practice_questions", "mean"),
        recent_practice_questions_total=("practice_questions", "sum"),
        recent_zero_attendance_days=("session_attended_min", lambda s: int((s == 0).sum())),
    )
    grouped["recent_attendance_rate"] = (
        grouped["recent_attendance_min_avg"] / config.expected_session_minutes
    ).clip(0, 1)
    return grouped.reset_index()


def post_quiz_activity_features(
    daily: pd.DataFrame,
    quiz_1_date: pd.Timestamp,
    as_of: pd.Timestamp,
    config: FeatureConfig,
) -> pd.DataFrame:
    post_quiz = daily[daily["date"].between(quiz_1_date, as_of)].copy()
    grouped = post_quiz.groupby("student_id").agg(
        post_quiz_days_observed=("date", "nunique"),
        post_quiz_sessions_attended=("session_attended_min", lambda s: int((s > 0).sum())),
        post_quiz_attendance_min_avg=("session_attended_min", "mean"),
        post_quiz_practice_questions_total=("practice_questions", "sum"),
        post_quiz_zero_attendance_days=("session_attended_min", lambda s: int((s == 0).sum())),
    )
    grouped["post_quiz_attendance_rate"] = (
        grouped["post_quiz_attendance_min_avg"] / config.expected_session_minutes
    ).clip(0, 1)
    return grouped.reset_index()


def note_activity_features(notes: pd.DataFrame, as_of: pd.Timestamp) -> pd.DataFrame:
    if notes.empty:
        return pd.DataFrame(columns=["student_id"])

    ordered_notes = notes.sort_values(["student_id", "date", "note_id"]).copy()
    ordered_notes["note_entry"] = ordered_notes.apply(format_note_entry, axis=1)
    grouped = notes.groupby("student_id").agg(
        notes_count=("note_id", "count"),
        latest_note_date=("date", "max"),
        latest_note_text=("note_text", "last"),
    )
    notes_history = ordered_notes.groupby("student_id")["note_entry"].apply("\n".join)
    grouped = grouped.join(notes_history.rename("notes_history"))
    grouped["days_since_latest_note"] = (as_of - grouped["latest_note_date"]).dt.days
    return grouped.reset_index()


def fill_feature_defaults(features: pd.DataFrame) -> pd.DataFrame:
    filled = features.copy()
    numeric_defaults = {
        "quiz_count": 0,
        "latest_quiz_number": 0,
        "days_until_next_quiz": 999,
        "recent_days_observed": 0,
        "recent_sessions_attended": 0,
        "recent_attendance_min_avg": 0,
        "recent_practice_questions_avg": 0,
        "recent_practice_questions_total": 0,
        "recent_zero_attendance_days": 0,
        "recent_attendance_rate": 0,
        "post_quiz_days_observed": 0,
        "post_quiz_sessions_attended": 0,
        "post_quiz_attendance_min_avg": 0,
        "post_quiz_practice_questions_total": 0,
        "post_quiz_zero_attendance_days": 0,
        "post_quiz_attendance_rate": 0,
        "notes_count": 0,
        "days_since_latest_note": 999,
    }
    for column, default in numeric_defaults.items():
        if column not in filled.columns:
            filled[column] = default
        filled[column] = filled[column].fillna(default)

    for column in ["latest_quiz_score", "previous_quiz_score", "quiz_score_delta", "latest_quiz_date"]:
        if column not in filled.columns:
            filled[column] = pd.NA

    if "has_quiz" not in filled.columns:
        filled["has_quiz"] = False
    filled["has_quiz"] = filled["has_quiz"].where(filled["has_quiz"].notna(), False).astype(bool)
    if "latest_note_text" not in filled.columns:
        filled["latest_note_text"] = ""
    if "notes_history" not in filled.columns:
        filled["notes_history"] = ""
    filled["latest_note_text"] = filled["latest_note_text"].fillna("")
    filled["notes_history"] = filled["notes_history"].fillna("")
    return filled


def format_note_entry(row: pd.Series) -> str:
    short_date = pd.Timestamp(row["date"]).strftime("%m-%d")
    return f"{short_date}: {row['note_text']}"

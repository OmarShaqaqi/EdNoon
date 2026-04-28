from __future__ import annotations

from pathlib import Path
import csv

import pandas as pd

from .config import FeedbackConfig


REQUIRED_LOG_COLUMNS = {
    "student_id",
    "student_name",
    "facilitator_email",
    "risk_score",
    "recommended_action",
    "status",
    "contact_method",
    "outcome_notes",
}


def analyze_feedback(
    queue_path: Path,
    log_path: Path,
    output_dir: Path,
    config: FeedbackConfig,
) -> dict[str, pd.DataFrame]:
    queue = pd.read_csv(queue_path, dtype={"student_id": str, "parent_phone": str})
    log = load_intervention_log(log_path)
    latest_log = latest_log_per_student(log)

    joined = queue.merge(
        latest_log,
        on=["student_id", "facilitator_email"],
        how="left",
        suffixes=("", "_feedback"),
    )
    joined["latest_status"] = joined["status"].fillna("not_started")
    joined["latest_contact_method"] = joined["contact_method"].fillna("")
    joined["latest_outcome_notes"] = joined["outcome_notes"].fillna("")
    joined["has_action"] = joined["latest_status"].isin(config.acted_statuses)
    joined["completed_action"] = joined["latest_status"].isin(config.completed_statuses)
    joined["needs_followup"] = joined["latest_status"].isin(config.followup_statuses)
    joined["needs_followup_or_not_started"] = joined["needs_followup"] | ~joined["has_action"]

    summary = build_summary(joined)
    facilitator_summary = build_facilitator_summary(joined)
    status_summary = build_status_summary(joined)
    followup = joined[joined["needs_followup"] | ~joined["has_action"]].copy()
    followup = followup.sort_values(["has_action", "risk_score"], ascending=[True, False])

    output_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_dir / "feedback_summary.csv", index=False)
    facilitator_summary.to_csv(output_dir / "feedback_by_facilitator.csv", index=False)
    status_summary.to_csv(output_dir / "feedback_by_status.csv", index=False)
    followup.to_csv(output_dir / "students_needing_followup.csv", index=False, quoting=csv.QUOTE_NONNUMERIC)

    return {
        "summary": summary,
        "facilitator_summary": facilitator_summary,
        "status_summary": status_summary,
        "followup": followup,
    }


def load_intervention_log(log_path: Path) -> pd.DataFrame:
    if not log_path.exists():
        raise FileNotFoundError(
            f"Intervention log not found: {log_path}. Export the Google Form response sheet as CSV "
            "and pass it with --log-path."
        )

    log = pd.read_csv(log_path, dtype={"student_id": str})
    missing = REQUIRED_LOG_COLUMNS - set(log.columns)
    if missing:
        raise ValueError(f"Intervention log is missing columns: {sorted(missing)}")

    log = log.copy()
    log["student_id"] = log["student_id"].astype(str).str.strip().str.upper()
    log["facilitator_email"] = log["facilitator_email"].astype(str).str.strip().str.lower()
    log["status"] = log["status"].fillna("").astype(str).str.strip()
    log["contact_method"] = log["contact_method"].fillna("").astype(str).str.strip()
    log["outcome_notes"] = log["outcome_notes"].fillna("").astype(str).str.strip()
    return log


def latest_log_per_student(log: pd.DataFrame) -> pd.DataFrame:
    if log.empty:
        return log
    timestamp_columns = [column for column in ["Timestamp", "timestamp", "logged_at"] if column in log.columns]
    if timestamp_columns:
        timestamp_column = timestamp_columns[0]
        log = log.copy()
        log["_feedback_timestamp"] = pd.to_datetime(log[timestamp_column], errors="coerce")
        return log.sort_values("_feedback_timestamp").groupby(["student_id", "facilitator_email"]).tail(1)
    return log.groupby(["student_id", "facilitator_email"]).tail(1)


def build_summary(joined: pd.DataFrame) -> pd.DataFrame:
    recommended = len(joined)
    acted = int(joined["has_action"].sum())
    completed = int(joined["completed_action"].sum())
    needs_followup = int((joined["needs_followup"] | ~joined["has_action"]).sum())
    return pd.DataFrame(
        [
            {
                "recommended_students": recommended,
                "students_with_any_action": acted,
                "intervention_coverage_rate": safe_rate(acted, recommended),
                "completed_interventions": completed,
                "completion_rate": safe_rate(completed, recommended),
                "students_needing_followup": needs_followup,
            }
        ]
    )


def build_facilitator_summary(joined: pd.DataFrame) -> pd.DataFrame:
    grouped = joined.groupby("facilitator_email").agg(
        recommended_students=("student_id", "count"),
        students_with_any_action=("has_action", "sum"),
        completed_interventions=("completed_action", "sum"),
        students_needing_followup=("needs_followup_or_not_started", "sum"),
    )
    grouped["intervention_coverage_rate"] = (
        grouped["students_with_any_action"] / grouped["recommended_students"]
    ).round(3)
    grouped["completion_rate"] = (
        grouped["completed_interventions"] / grouped["recommended_students"]
    ).round(3)
    return grouped.reset_index()


def build_status_summary(joined: pd.DataFrame) -> pd.DataFrame:
    return (
        joined["latest_status"]
        .value_counts(dropna=False)
        .rename_axis("status")
        .reset_index(name="students")
    )


def safe_rate(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 3)

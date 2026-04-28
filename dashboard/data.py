from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class DashboardPaths:
    """Resolved input files used by the read-only manager dashboard."""

    risk_scores: Path
    action_queue: Path
    feedback_summary: Path
    feedback_by_facilitator: Path
    students_needing_followup: Path


def resolve_dashboard_paths(as_of: str, root: Path = PROJECT_ROOT) -> DashboardPaths:
    """Build paths for the date-specific pipeline outputs the dashboard reads."""
    return DashboardPaths(
        risk_scores=root / "outputs" / "risk" / f"student_risk_scores_{as_of}.csv",
        action_queue=root / "outputs" / "interventions" / f"facilitator_action_queue_{as_of}.csv",
        feedback_summary=root / "outputs" / "feedback" / "feedback_summary.csv",
        feedback_by_facilitator=root / "outputs" / "feedback" / "feedback_by_facilitator.csv",
        students_needing_followup=root / "outputs" / "feedback" / "students_needing_followup.csv",
    )


def available_run_dates(root: Path = PROJECT_ROOT) -> list[str]:
    """Return dates that have risk-score output files, newest first."""
    risk_dir = root / "outputs" / "risk"
    if not risk_dir.exists():
        return []

    dates: list[str] = []
    for path in risk_dir.glob("student_risk_scores_*.csv"):
        dates.append(path.stem.replace("student_risk_scores_", ""))
    return sorted(dates, reverse=True)


def load_dashboard_data(paths: DashboardPaths) -> dict[str, pd.DataFrame]:
    """Load all dashboard inputs, tolerating missing feedback files during first run."""
    risk = read_csv(paths.risk_scores, required=True)
    queue = read_csv(paths.action_queue, required=True)
    feedback_summary = read_csv(paths.feedback_summary, required=False)
    feedback_by_facilitator = read_csv(paths.feedback_by_facilitator, required=False)
    followup = read_csv(paths.students_needing_followup, required=False)
    manager_view = build_manager_view(risk, queue, followup)

    return {
        "risk": risk,
        "queue": queue,
        "manager_view": manager_view,
        "feedback_summary": feedback_summary,
        "feedback_by_facilitator": feedback_by_facilitator,
        "followup": followup,
    }


def read_csv(path: Path, required: bool) -> pd.DataFrame:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Required dashboard input is missing: {path}")
        return pd.DataFrame()
    return pd.read_csv(path, dtype={"student_id": str, "parent_phone": str})


def build_manager_view(risk: pd.DataFrame, queue: pd.DataFrame, followup: pd.DataFrame) -> pd.DataFrame:
    """Combine risk, action queue, and feedback status into one manager table."""
    view = risk.copy()

    action_columns = [
        "student_id",
        "today_action",
        "action_priority",
        "queue_rank",
        "recommended_action",
        "message_draft",
        "needs_human_review",
        "review_reason",
        "update_form_link",
    ]
    existing_action_columns = [column for column in action_columns if column in queue.columns]
    if existing_action_columns:
        view = view.merge(queue[existing_action_columns], on="student_id", how="left")

    if not followup.empty:
        feedback_columns = [
            "student_id",
            "latest_status",
            "latest_contact_method",
            "latest_outcome_notes",
            "has_action",
            "completed_action",
            "needs_followup",
        ]
        existing_feedback_columns = [column for column in feedback_columns if column in followup.columns]
        if existing_feedback_columns:
            view = view.merge(
                followup[existing_feedback_columns].drop_duplicates("student_id"),
                on="student_id",
                how="left",
            )

    view["today_action"] = clean_boolean_column(view, "today_action")
    view["latest_status"] = view.get("latest_status", "not_started").fillna("not_started")
    view["has_action"] = clean_boolean_column(view, "has_action")
    view["completed_action"] = clean_boolean_column(view, "completed_action")
    view["needs_followup"] = clean_boolean_column(view, "needs_followup")
    return view


def clean_boolean_column(data: pd.DataFrame, column: str) -> pd.Series:
    """Normalize missing or string-like boolean columns from CSV outputs."""
    if column not in data:
        return pd.Series(False, index=data.index)
    return data[column].map(parse_bool).fillna(False).astype(bool)


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if pd.isna(value):
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def filter_students(
    students: pd.DataFrame,
    campuses: list[str],
    facilitators: list[str],
    grades: list[int],
    risk_levels: list[str],
    only_today_actions: bool,
    only_missing_intervention: bool,
) -> pd.DataFrame:
    """Apply dashboard filters without mutating the loaded data."""
    filtered = students.copy()

    if campuses:
        filtered = filtered[filtered["campus_id"].isin(campuses)]
    if facilitators:
        filtered = filtered[filtered["facilitator_email"].isin(facilitators)]
    if grades:
        filtered = filtered[filtered["grade"].isin(grades)]
    if risk_levels:
        filtered = filtered[filtered["risk_level"].isin(risk_levels)]
    if only_today_actions and "today_action" in filtered:
        filtered = filtered[filtered["today_action"]]
    if only_missing_intervention and "has_action" in filtered:
        filtered = filtered[~filtered["has_action"]]

    return filtered


def metric_summary(students: pd.DataFrame, queue: pd.DataFrame, feedback_summary: pd.DataFrame) -> dict[str, str]:
    """Create top-level metrics in display-ready form."""
    total_students = len(students)
    high_risk = int(students["risk_level"].isin(["high", "critical"]).sum()) if "risk_level" in students else 0
    queued = len(queue)
    today_actions = int(queue["today_action"].fillna(False).astype(bool).sum()) if "today_action" in queue else 0

    coverage = "0.0%"
    needs_followup = "0"
    if not feedback_summary.empty:
        first_row = feedback_summary.iloc[0]
        coverage = format_percent(first_row.get("intervention_coverage_rate", 0))
        needs_followup = str(int(first_row.get("students_needing_followup", 0)))

    return {
        "total_students": str(total_students),
        "high_risk": str(high_risk),
        "queued": str(queued),
        "today_actions": str(today_actions),
        "coverage": coverage,
        "needs_followup": needs_followup,
    }


def campus_summary(students: pd.DataFrame) -> pd.DataFrame:
    """Aggregate risk and intervention visibility by campus."""
    if students.empty:
        return pd.DataFrame()

    grouped = students.groupby("campus_id").agg(
        students=("student_id", "count"),
        high_or_critical=("risk_level", lambda values: values.isin(["high", "critical"]).sum()),
        today_actions=("today_action", "sum"),
        missing_intervention=("has_action", lambda values: (~values).sum()),
        avg_risk=("risk_score", "mean"),
    )
    grouped["avg_risk"] = grouped["avg_risk"].round(1)
    return grouped.reset_index().sort_values(["high_or_critical", "avg_risk"], ascending=[False, False])


def facilitator_workload(students: pd.DataFrame) -> pd.DataFrame:
    """Aggregate queue pressure by facilitator for manager triage."""
    if students.empty:
        return pd.DataFrame()

    grouped = students.groupby("facilitator_email").agg(
        students=("student_id", "count"),
        queued_today=("today_action", "sum"),
        high_or_critical=("risk_level", lambda values: values.isin(["high", "critical"]).sum()),
        missing_intervention=("has_action", lambda values: (~values).sum()),
        avg_risk=("risk_score", "mean"),
    )
    grouped["avg_risk"] = grouped["avg_risk"].round(1)
    return grouped.reset_index().sort_values(["queued_today", "high_or_critical"], ascending=[False, False])


def manager_alerts(students: pd.DataFrame) -> list[str]:
    """Generate simple operational alerts from the current filtered view."""
    if students.empty:
        return ["No students match the selected filters."]

    alerts: list[str] = []
    high_unacted = students[
        students["risk_level"].isin(["high", "critical"]) & ~students["has_action"]
    ]
    if not high_unacted.empty:
        alerts.append(f"{len(high_unacted)} high/critical students still have no logged intervention.")

    workload = facilitator_workload(students)
    if not workload.empty:
        busiest = workload.iloc[0]
        if int(busiest["queued_today"]) > 0:
            alerts.append(
                f"{busiest['facilitator_email']} has the heaviest queue today "
                f"({int(busiest['queued_today'])} students)."
            )

    campuses = campus_summary(students)
    if not campuses.empty:
        campus = campuses.iloc[0]
        alerts.append(
            f"{campus['campus_id']} has the highest current risk load "
            f"({int(campus['high_or_critical'])} high/critical students)."
        )

    return alerts


def format_percent(value: object) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "0.0%"

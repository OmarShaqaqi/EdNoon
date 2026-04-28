from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Streamlit runs this file as a script, so add the project root to imports.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dashboard.data import (
    available_run_dates,
    campus_summary,
    facilitator_workload,
    filter_students,
    load_dashboard_data,
    manager_alerts,
    metric_summary,
    resolve_dashboard_paths,
)


st.set_page_config(
    page_title="Boon Intervention Manager",
    page_icon=":bar_chart:",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def cached_dashboard_data(as_of: str) -> dict:
    """Cache CSV reads so filters feel instant during a live demo."""
    paths = resolve_dashboard_paths(as_of)
    return load_dashboard_data(paths)


def main() -> None:
    st.title("Boon Intervention Manager")
    st.caption("Read-only monitoring dashboard for risk, facilitator workload, and feedback coverage.")

    run_dates = available_run_dates()
    if not run_dates:
        st.error("No risk output files found. Run the pipeline first.")
        st.code(".venv/bin/python run_pipeline.py --as-of 2025-10-14")
        return

    with st.sidebar:
        st.header("Filters")
        as_of = st.selectbox("Run date", run_dates, index=0)

    data = cached_dashboard_data(as_of)
    students = data["manager_view"]
    queue = data["queue"]
    feedback_summary = data["feedback_summary"]

    with st.sidebar:
        campuses = st.multiselect("Campus", sorted(students["campus_id"].dropna().unique()))
        facilitators = st.multiselect(
            "Facilitator",
            sorted(students["facilitator_email"].dropna().unique()),
        )
        grades = st.multiselect("Grade", sorted(students["grade"].dropna().unique()))
        risk_levels = st.multiselect(
            "Risk level",
            ["critical", "high", "medium", "low"],
            default=["critical", "high", "medium"],
        )
        only_today_actions = st.toggle("Only today's action queue", value=False)
        only_missing_intervention = st.toggle("Only missing intervention", value=False)

    filtered = filter_students(
        students=students,
        campuses=campuses,
        facilitators=facilitators,
        grades=grades,
        risk_levels=risk_levels,
        only_today_actions=only_today_actions,
        only_missing_intervention=only_missing_intervention,
    )

    render_metrics(students, queue, feedback_summary)
    render_alerts(filtered)
    render_charts(filtered)
    render_student_table(filtered)


def render_metrics(students, queue, feedback_summary) -> None:
    summary = metric_summary(students, queue, feedback_summary)
    metric_columns = st.columns(6)
    metric_columns[0].metric("Students", summary["total_students"])
    metric_columns[1].metric("High/Critical", summary["high_risk"])
    metric_columns[2].metric("Queued", summary["queued"])
    metric_columns[3].metric("Today Actions", summary["today_actions"])
    metric_columns[4].metric("Coverage", summary["coverage"])
    metric_columns[5].metric("Need Follow-up", summary["needs_followup"])


def render_alerts(students) -> None:
    st.subheader("Manager Alerts")
    for alert in manager_alerts(students):
        st.warning(alert)


def render_charts(students) -> None:
    left, right = st.columns(2)

    with left:
        st.subheader("Campus Risk Load")
        campus = campus_summary(students)
        if campus.empty:
            st.info("No campus data for the selected filters.")
        else:
            st.dataframe(campus, use_container_width=True, hide_index=True)
            st.bar_chart(campus.set_index("campus_id")[["high_or_critical", "today_actions"]])

    with right:
        st.subheader("Facilitator Workload")
        workload = facilitator_workload(students)
        if workload.empty:
            st.info("No facilitator data for the selected filters.")
        else:
            st.dataframe(workload, use_container_width=True, hide_index=True)
            st.bar_chart(workload.set_index("facilitator_email")[["queued_today", "missing_intervention"]])


def render_student_table(students) -> None:
    st.subheader("Student Detail")
    columns = [
        "student_id",
        "student_name",
        "campus_id",
        "facilitator_email",
        "grade",
        "parent_phone",
        "risk_score",
        "risk_level",
        "today_action",
        "recommended_action",
        "latest_status",
        "recent_attendance_rate",
        "recent_practice_questions_avg",
        "latest_quiz_score",
        "risk_reasons",
        "update_form_link",
    ]
    visible_columns = [column for column in columns if column in students.columns]
    table = students[visible_columns].sort_values("risk_score", ascending=False)

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "risk_score": st.column_config.ProgressColumn(
                "risk_score",
                min_value=0,
                max_value=100,
                format="%.1f",
            ),
            "recent_attendance_rate": st.column_config.ProgressColumn(
                "recent_attendance_rate",
                min_value=0,
                max_value=1,
                format="%.0f%%",
            ),
            "update_form_link": st.column_config.LinkColumn("update_form_link"),
        },
    )


if __name__ == "__main__":
    main()

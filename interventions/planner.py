from __future__ import annotations

from pathlib import Path

import pandas as pd

from .action_llm import ActionPlannerLLM
from .config import InterventionConfig


OUTPUT_COLUMNS = [
    "student_id",
    "student_name",
    "campus_id",
    "facilitator_email",
    "parent_phone",
    "parent_phone_valid",
    "risk_score",
    "risk_level",
    "action_priority",
    "queue_rank",
    "today_action",
    "recommended_action",
    "risk_reasons",
    "message_draft",
    "needs_human_review",
    "review_reason",
    "action_plan_source",
]


def build_action_queue(scored: pd.DataFrame, config: InterventionConfig, action_planner: ActionPlannerLLM | None = None) -> pd.DataFrame:
    queue = scored.copy()
    queue["action_priority"] = queue.apply(action_priority, axis=1)
    queue = queue[queue["action_priority"].ne("monitor")].copy()

    action_planner = action_planner or ActionPlannerLLM(config)
    action_results = pd.Series(action_planner.plan_rows(queue), index=queue.index)
    queue["recommended_action"] = action_results.map(lambda result: result.recommended_action)
    queue["message_draft"] = action_results.map(lambda result: result.message_draft)
    queue["needs_human_review"] = action_results.map(lambda result: result.needs_human_review)
    queue["review_reason"] = action_results.map(lambda result: result.review_reason)
    queue["action_plan_source"] = action_results.map(lambda result: result.source)

    queue = queue.sort_values(["facilitator_email", "risk_score"], ascending=[True, False])
    queue["queue_rank"] = queue.groupby("facilitator_email").cumcount() + 1
    queue["today_action"] = queue["queue_rank"].le(config.max_daily_actions_per_facilitator)
    queue = queue.sort_values(["today_action", "facilitator_email", "queue_rank"], ascending=[False, True, True])
    return queue[OUTPUT_COLUMNS]


def action_priority(row: pd.Series) -> str:
    if row["risk_level"] == "critical":
        return "today"
    if row["risk_level"] == "high":
        return "within_48h"
    if row["risk_level"] == "medium":
        return "nudge_or_monitor"
    return "monitor"


def write_facilitator_digest(path: Path, queue: pd.DataFrame) -> None:
    lines = ["# Facilitator Action Digest", ""]
    today = queue[queue["today_action"]].copy()
    if today.empty:
        lines.append("No actions queued for today.")
    for facilitator_email, group in today.groupby("facilitator_email"):
        lines.extend([f"## {facilitator_email}", ""])
        for row in group.itertuples(index=False):
            review = f"\n- Review: {row.review_reason}" if row.needs_human_review else ""
            lines.extend(
                [
                    f"### {row.queue_rank}. {row.student_name} ({row.student_id})",
                    f"- Campus: {row.campus_id}",
                    f"- Parent: {row.parent_phone}",
                    f"- Risk: {row.risk_score} ({row.risk_level})",
                    f"- Why: {row.risk_reasons}",
                    f"- Action: {row.recommended_action}{review}",
                    f"- Message: {row.message_draft}",
                    "",
                ]
            )
    path.write_text("\n".join(lines), encoding="utf-8")

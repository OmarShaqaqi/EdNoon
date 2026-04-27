from __future__ import annotations

import argparse
from pathlib import Path

from interventions.config import InterventionConfig
from interventions.pipeline import plan_interventions


def main() -> None:
    parser = argparse.ArgumentParser(description="Build facilitator intervention action queue.")
    parser.add_argument(
        "--risk-path",
        type=Path,
        default=Path("outputs/risk/student_risk_scores_2025-10-14.csv"),
    )
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/interventions"))
    args = parser.parse_args()

    queue = plan_interventions(args.risk_path, args.output_dir, InterventionConfig())
    today = queue[queue["today_action"]]
    print(f"Queued {len(queue)} students for intervention")
    print(f"Today actions: {len(today)}")
    print(today[["facilitator_email", "queue_rank", "student_id", "student_name", "risk_score", "action_priority", "recommended_action"]].head(12).to_string(index=False))


if __name__ == "__main__":
    main()


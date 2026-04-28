from __future__ import annotations

import argparse
from pathlib import Path

from feedback.config import FeedbackConfig
from feedback.pipeline import analyze_feedback


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze intervention feedback logs.")
    parser.add_argument(
        "--queue-path",
        type=Path,
        default=Path("outputs/interventions/facilitator_action_queue_2025-10-14.csv"),
    )
    parser.add_argument("--log-path", type=Path, default=Path("data/intervention_log.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/feedback"))
    args = parser.parse_args()

    outputs = analyze_feedback(args.queue_path, args.log_path, args.output_dir, FeedbackConfig())
    print("Feedback summary")
    print(outputs["summary"].to_string(index=False))
    print("\nBy facilitator")
    print(outputs["facilitator_summary"].to_string(index=False))
    print(f"\nOutputs written to {args.output_dir}")


if __name__ == "__main__":
    main()


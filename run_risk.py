from __future__ import annotations

import argparse
from pathlib import Path

from risk.config import RiskConfig
from risk.pipeline import score_risk


def main() -> None:
    parser = argparse.ArgumentParser(description="Score student risk from engineered features.")
    parser.add_argument("--features-path", type=Path, default=Path("outputs/features/student_features_2025-10-14.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/risk"))
    args = parser.parse_args()

    scored = score_risk(args.features_path, args.output_dir, RiskConfig())
    print(f"Scored risk for {len(scored)} students")
    print(scored[["student_id", "student_name", "risk_score", "risk_level", "risk_reasons"]].head(10).to_string(index=False))


if __name__ == "__main__":
    main()

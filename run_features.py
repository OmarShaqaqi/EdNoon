from __future__ import annotations

import argparse
from pathlib import Path

from features.config import FeatureConfig
from features.pipeline import build_student_features


def main() -> None:
    parser = argparse.ArgumentParser(description="Build student-level feature table.")
    parser.add_argument("--input-dir", type=Path, default=Path("outputs/ingestion/clean"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/features"))
    parser.add_argument("--as-of", default="2025-10-14")
    parser.add_argument("--quiz-1-date", default="2025-10-10")
    args = parser.parse_args()

    config = FeatureConfig(as_of_date=args.as_of, quiz_1_date=args.quiz_1_date)
    features = build_student_features(args.input_dir, args.output_dir, config)
    print(f"Built features for {len(features)} students")
    print(f"Output: {args.output_dir / f'student_features_{args.as_of}.csv'}")


if __name__ == "__main__":
    main()


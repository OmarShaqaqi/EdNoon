from __future__ import annotations

import argparse
from pathlib import Path

from ingestion.pipeline import run_ingestion


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Boon data ingestion layer.")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/ingestion"))
    args = parser.parse_args()

    report = run_ingestion(args.data_dir, args.output_dir)
    print("Ingestion complete")
    for dataset, loaded in report.loaded_rows.items():
        output = report.output_rows.get(dataset, 0)
        print(f"- {dataset}: loaded {loaded}, output {output}")
    print(f"Warnings: {len(report.warnings)}")
    print(f"Errors/quarantines: {len(report.errors)}")
    print(f"Report: {args.output_dir / 'quality_report.md'}")


if __name__ == "__main__":
    main()


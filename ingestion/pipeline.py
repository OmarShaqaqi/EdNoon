from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .cleaners import clean_daily_metrics, clean_facilitator_notes, clean_student_metadata
from .quality import QualityReport
from .schemas import REQUIRED_COLUMNS, SourceFiles


def run_ingestion(data_dir: Path, output_dir: Path) -> QualityReport:
    report = QualityReport()
    sources = SourceFiles()

    raw_metadata = read_required_csv(data_dir / sources.student_metadata, "student_metadata", report)
    raw_daily = read_required_csv(data_dir / sources.student_daily_metrics, "student_daily_metrics", report)
    raw_notes = read_required_csv(data_dir / sources.facilitator_notes, "facilitator_notes", report)

    metadata = clean_student_metadata(raw_metadata, report)
    known_student_ids = set(metadata["student_id"])
    daily = clean_daily_metrics(raw_daily, known_student_ids, report)
    notes = clean_facilitator_notes(raw_notes, known_student_ids, report)

    report.output_rows = {
        "student_metadata": len(metadata),
        "student_daily_metrics": len(daily),
        "facilitator_notes": len(notes),
    }

    write_outputs(output_dir, metadata, daily, notes, report)
    return report


def read_required_csv(path: Path, dataset: str, report: QualityReport) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing required source file: {path}")

    df = pd.read_csv(path)
    report.loaded_rows[dataset] = len(df)

    missing_columns = REQUIRED_COLUMNS[dataset] - set(df.columns)
    if missing_columns:
        raise ValueError(f"{dataset} is missing required columns: {sorted(missing_columns)}")
    return df


def write_outputs(
    output_dir: Path,
    metadata: pd.DataFrame,
    daily: pd.DataFrame,
    notes: pd.DataFrame,
    report: QualityReport,
) -> None:
    clean_dir = output_dir / "clean"
    clean_dir.mkdir(parents=True, exist_ok=True)

    metadata.to_csv(clean_dir / "student_metadata_clean.csv", index=False)
    daily.to_csv(clean_dir / "student_daily_metrics_clean.csv", index=False)
    notes.to_csv(clean_dir / "facilitator_notes_clean.csv", index=False)

    (output_dir / "quality_report.json").write_text(
        json.dumps(report.as_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (output_dir / "quality_report.md").write_text(render_markdown_report(report), encoding="utf-8")


def render_markdown_report(report: QualityReport) -> str:
    lines = ["# Ingestion Quality Report", "", "## Row Counts", ""]
    for dataset, loaded in report.loaded_rows.items():
        output = report.output_rows.get(dataset, 0)
        lines.append(f"- {dataset}: loaded {loaded}, output {output}")

    lines.extend(["", "## Warnings", ""])
    if report.warnings:
        for item in report.warnings:
            detail = f" - {item['detail']}" if item.get("detail") else ""
            lines.append(f"- {item['dataset']}: {item['issue']} ({item['count']}){detail}")
    else:
        lines.append("- None")

    lines.extend(["", "## Errors / Quarantined Rows", ""])
    if report.errors:
        for item in report.errors:
            detail = f" - {item['detail']}" if item.get("detail") else ""
            lines.append(f"- {item['dataset']}: {item['issue']} ({item['count']}){detail}")
    else:
        lines.append("- None")

    return "\n".join(lines) + "\n"


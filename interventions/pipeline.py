from __future__ import annotations

from pathlib import Path
import csv

import pandas as pd

from .config import InterventionConfig
from .planner import build_action_queue, write_facilitator_digest


def plan_interventions(input_path: Path, output_dir: Path, config: InterventionConfig) -> pd.DataFrame:
    scored = pd.read_csv(input_path, dtype={"student_id": str, "parent_phone": str})
    queue = build_action_queue(scored, config)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / input_path.name.replace("student_risk_scores", "facilitator_action_queue")
    queue.to_csv(output_path, index=False, quoting=csv.QUOTE_NONNUMERIC)
    write_facilitator_digest(output_dir / output_path.name.replace(".csv", ".md"), queue)
    write_facilitator_csvs(output_dir / "facilitators", queue, output_path.stem)
    return queue


def write_facilitator_csvs(output_dir: Path, queue: pd.DataFrame, queue_name: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for facilitator_email, group in queue.groupby("facilitator_email"):
        file_name = f"{safe_file_name(facilitator_email)}_{queue_name}.csv"
        group.to_csv(output_dir / file_name, index=False, quoting=csv.QUOTE_NONNUMERIC)


def safe_file_name(value: str) -> str:
    safe = "".join(char if char.isalnum() else "_" for char in str(value).lower())
    return "_".join(part for part in safe.split("_") if part)

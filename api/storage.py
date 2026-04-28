from __future__ import annotations

import csv
from pathlib import Path

from .schemas import InterventionLogRecord


LOG_COLUMNS = [
    "timestamp",
    "student_id",
    "student_name",
    "facilitator_email",
    "risk_score",
    "recommended_action",
    "status",
    "contact_method",
    "outcome_notes",
    "source",
]


def append_intervention_log(record: InterventionLogRecord, log_path: Path) -> None:
    """Append one webhook event to the intervention log CSV."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not log_path.exists() or log_path.stat().st_size == 0

    with log_path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=LOG_COLUMNS, quoting=csv.QUOTE_NONNUMERIC)
        if write_header:
            writer.writeheader()
        writer.writerow(record.model_dump())


def count_log_rows(log_path: Path) -> int:
    """Return the number of stored feedback rows, excluding the CSV header."""
    if not log_path.exists():
        return 0
    with log_path.open(newline="", encoding="utf-8") as file:
        return max(sum(1 for _ in file) - 1, 0)

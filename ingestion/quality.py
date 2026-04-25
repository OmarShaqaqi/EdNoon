from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class QualityReport:
    loaded_rows: dict[str, int] = field(default_factory=dict)
    output_rows: dict[str, int] = field(default_factory=dict)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)

    def warn(self, dataset: str, issue: str, count: int, detail: str = "") -> None:
        if count:
            self.warnings.append(
                {"dataset": dataset, "issue": issue, "count": int(count), "detail": detail}
            )

    def error(self, dataset: str, issue: str, count: int, detail: str = "") -> None:
        if count:
            self.errors.append(
                {"dataset": dataset, "issue": issue, "count": int(count), "detail": detail}
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "loaded_rows": self.loaded_rows,
            "output_rows": self.output_rows,
            "warnings": self.warnings,
            "errors": self.errors,
        }


from __future__ import annotations

from pathlib import Path
import csv

import pandas as pd

from .components import add_risk_components
from .config import RiskConfig
from .scoring import add_final_risk_score


def score_risk(input_path: Path, output_dir: Path, config: RiskConfig) -> pd.DataFrame:
    features = pd.read_csv(input_path, dtype={"student_id": str, "parent_phone": str})
    scored = add_risk_components(features, config)
    scored = add_final_risk_score(scored, config)

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / input_path.name.replace("student_features", "student_risk_scores")
    scored.to_csv(output_path, index=False, quoting=csv.QUOTE_NONNUMERIC)
    return scored

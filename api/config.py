from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class WebhookConfig:
    """Runtime settings for the Zapier webhook receiver."""

    log_path: Path = Path(os.getenv("INTERVENTION_LOG_PATH", "data/intervention_log.csv"))
    api_key: str = os.getenv("WEBHOOK_API_KEY", "")

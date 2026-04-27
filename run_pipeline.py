from __future__ import annotations

import argparse
import os
from pathlib import Path

from features.config import FeatureConfig
from features.pipeline import build_student_features
from ingestion.pipeline import run_ingestion
from integrations.drive_upload import upload_folder_to_drive
from interventions.config import InterventionConfig
from interventions.pipeline import plan_interventions
from risk.config import RiskConfig
from risk.pipeline import score_risk


def main() -> None:
    load_env_file()

    parser = argparse.ArgumentParser(description="Run the Boon intervention pipeline end to end.")
    parser.add_argument("--as-of", default="2025-10-14")
    parser.add_argument("--data-dir", type=Path, default=Path("data"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--upload-drive", action="store_true", help="Upload facilitator CSVs to Google Drive.")
    parser.add_argument(
        "--drive-folder-id",
        default=os.environ.get("GOOGLE_DRIVE_FOLDER_ID"),
        help="Google Drive folder ID watched by Zapier.",
    )
    parser.add_argument(
        "--drive-service-account",
        type=Path,
        default=Path(os.environ["GOOGLE_APPLICATION_CREDENTIALS"])
        if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        else None,
        help="Path to Google service account JSON.",
    )
    parser.add_argument(
        "--drive-oauth-client-secret",
        type=Path,
        default=Path(os.environ["GOOGLE_OAUTH_CLIENT_SECRET"])
        if os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
        else None,
        help="Path to Google OAuth desktop client JSON.",
    )
    parser.add_argument(
        "--drive-oauth-token",
        type=Path,
        default=Path(os.environ["GOOGLE_OAUTH_TOKEN"])
        if os.environ.get("GOOGLE_OAUTH_TOKEN")
        else Path("token.json"),
        help="Path where OAuth user token should be stored.",
    )
    args = parser.parse_args()

    ingestion_dir = args.output_dir / "ingestion"
    clean_dir = ingestion_dir / "clean"
    features_dir = args.output_dir / "features"
    risk_dir = args.output_dir / "risk"
    interventions_dir = args.output_dir / "interventions"

    print("1/4 Ingesting data...")
    ingestion_report = run_ingestion(args.data_dir, ingestion_dir)

    print("2/4 Building features...")
    feature_config = FeatureConfig(as_of_date=args.as_of)
    features = build_student_features(clean_dir, features_dir, feature_config)
    features_path = features_dir / f"student_features_{args.as_of}.csv"

    print("3/4 Scoring risk...")
    scored = score_risk(features_path, risk_dir, RiskConfig())
    risk_path = risk_dir / f"student_risk_scores_{args.as_of}.csv"

    print("4/4 Planning interventions...")
    queue = plan_interventions(risk_path, interventions_dir, InterventionConfig())
    facilitator_folder = interventions_dir / "facilitators"

    print_summary(ingestion_report, features, scored, queue, facilitator_folder)

    if args.upload_drive:
        if not args.drive_folder_id:
            raise ValueError("Drive upload requested but --drive-folder-id / GOOGLE_DRIVE_FOLDER_ID is missing.")
        print("Uploading facilitator CSVs to Google Drive...")
        uploads = upload_folder_to_drive(
            local_folder=facilitator_folder,
            drive_folder_id=args.drive_folder_id,
            service_account_path=args.drive_service_account,
            oauth_client_secret_path=args.drive_oauth_client_secret,
            oauth_token_path=args.drive_oauth_token,
        )
        print(f"Uploaded {len(uploads)} files to Google Drive.")
        for result in uploads:
            link = f" -> {result.web_view_link}" if result.web_view_link else ""
            print(f"- {result.drive_file_name}{link}")
    else:
        print(f"Drive upload skipped. Upload this folder to trigger Zapier: {facilitator_folder}")


def print_summary(ingestion_report, features, scored, queue, facilitator_folder: Path) -> None:
    today_actions = int(queue["today_action"].sum()) if not queue.empty else 0
    print("\nPipeline summary")
    print(f"- Metadata rows loaded: {ingestion_report.loaded_rows.get('student_metadata', 0)}")
    print(f"- Students featured: {len(features)}")
    print(f"- Students risk-scored: {len(scored)}")
    print(f"- Students queued for intervention: {len(queue)}")
    print(f"- Today actions: {today_actions}")
    print(f"- Facilitator CSV folder: {facilitator_folder}")


def load_env_file() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(dotenv_path=Path(".env"))


if __name__ == "__main__":
    main()

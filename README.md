# Boon Academy Intervention System

This project is a runnable case-study system for improving student intervention coverage before Quiz 2.

The core idea:

> Give each facilitator a small, prioritized, actionable queue instead of asking them to inspect raw data and decide who needs help.

The system ingests operational CSVs, builds student-level features, scores risk with transparent weighted rules, uses LLMs where free-text judgment is useful, generates intervention queues, uploads facilitator-specific CSVs to Google Drive, and lets Zapier deliver each facilitator their own Google Sheet.

## Architecture

```text
Raw CSV data
  -> ingestion
  -> feature engineering
  -> risk scoring
  -> intervention planning
  -> facilitator CSVs
  -> Google Drive upload
  -> Zapier sends facilitator Sheets
```

## Main Run Command

Install dependencies:

```bash
.venv/bin/pip install -r requirements.txt
```

Run locally without Drive upload:

```bash
.venv/bin/python run_pipeline.py --as-of 2025-10-14
```

Run and upload facilitator CSVs to the Drive folder watched by Zapier:

```bash
.venv/bin/python run_pipeline.py --as-of 2025-10-14 --upload-drive
```

## Required `.env`

For OpenAI + Drive upload:

```text
OPENAI_API_KEY=...
GOOGLE_DRIVE_FOLDER_ID=...
GOOGLE_OAUTH_CLIENT_SECRET=/absolute/path/to/google-oauth-client.json
GOOGLE_OAUTH_TOKEN=token.json
```

`token.json` is generated after the first Google OAuth login. Do not commit `.env`, OAuth JSONs, or `token.json`.

## Outputs

Ingestion:

- `outputs/ingestion/clean/student_metadata_clean.csv`
- `outputs/ingestion/clean/student_daily_metrics_clean.csv`
- `outputs/ingestion/clean/facilitator_notes_clean.csv`
- `outputs/ingestion/quality_report.md`

Features:

- `outputs/features/student_features_2025-10-14.csv`

Risk:

- `outputs/risk/student_risk_scores_2025-10-14.csv`

Interventions:

- `outputs/interventions/facilitator_action_queue_2025-10-14.csv`
- `outputs/interventions/facilitator_action_queue_2025-10-14.md`
- `outputs/interventions/facilitators/*.csv`

Template:

- `templates/facilitator_queue_template.xlsx`

## Layer Summary

### Ingestion

Validates required columns, normalizes IDs/emails/phones/dates, handles missing activity data, and creates a quality report. Raw data remains untouched.

### Features

Builds one row per student: quiz status, recent attendance, recent practice, post-quiz behavior, note history, target gap, and days until next quiz. `days_until_next_quiz` is computed from configured quiz dates because the source column is shifted before Quiz 1.

### Risk

Scores risk as a normalized weighted average over available components:

- quiz score
- quiz trend
- attendance
- practice
- notes
- urgency

Unavailable signals are skipped, not treated as low risk.

### LLM Use

The LLM is used where text judgment matters:

- facilitator notes -> note risk, confidence, reason, signals
- intervention context -> recommended action + Arabic parent message

LLM calls run asynchronously with progress bars so large student batches do not run one request at a time.

If API access is unavailable, the system still runs with deterministic fallbacks and marks the source.

### Interventions

Creates an action queue with:

- student owner
- risk score/level
- action priority
- recommended action
- Arabic message draft
- human review flags
- one CSV per facilitator

### Zapier

Zapier handles workflow delivery:

1. Watch the Drive folder for facilitator CSV files.
2. Copy the Google Sheet template.
3. Insert facilitator rows.
4. Email each facilitator their own Sheet link.

This keeps Python as the intelligence layer and Zapier as the workflow glue.

## Success Metrics

Primary:

- intervention coverage: recommended students with a completed status
- target: move from about 30% to 80%+

Secondary:

- time to first action
- facilitator workload per day
- parent response rate
- invalid phone / no-answer rate
- attendance recovery before Quiz 2
- practice recovery before Quiz 2
- Quiz 2 score improvement

## Feedback Loop

Facilitator Sheets should include editable tracking columns:

- `status`
- `contact_method`
- `outcome_notes`
- `updated_at`

Zapier can append those updates to a master intervention log. Later, the pipeline can ingest that log to evaluate which actions worked and improve future recommendations.

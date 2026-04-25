# Data Ingestion Layer

This layer converts messy operational CSV exports into clean, validated tables for the later risk-scoring system.

Run:

```bash
.venv/bin/python run_ingestion.py
```

Inputs:

- `data/student_metadata.csv`
- `data/student_daily_metrics.csv`
- `data/facilitator_notes.csv`

Outputs:

- `outputs/ingestion/clean/student_metadata_clean.csv`
- `outputs/ingestion/clean/student_daily_metrics_clean.csv`
- `outputs/ingestion/clean/facilitator_notes_clean.csv`
- `outputs/ingestion/quality_report.md`
- `outputs/ingestion/quality_report.json`

Design principles:

- Keep raw data untouched.
- Validate required columns before cleaning.
- Normalize IDs, emails, dates, phone numbers, and numeric fields.
- Impute missing activity fields with paired-signal logic:
  - If `session_attended_min` is missing and `practice_questions` is `0`, fill session minutes with `0`.
  - If `session_attended_min` is missing and `practice_questions` is not `0`, fill session minutes with that student's average.
  - If `practice_questions` is missing and `session_attended_min` is `0`, fill practice questions with `0`.
  - If `practice_questions` is missing and `session_attended_min` is not `0`, fill practice questions with that student's average.
- Drop only rows that cannot be trusted, such as invalid dates or unknown students.
- Report every cleanup decision so operators can fix upstream data quality.

Current data quality findings:

- 200 student metadata rows loaded and cleaned.
- 2,000 daily metric rows loaded and cleaned.
- 180 facilitator notes loaded and cleaned.
- 1 parent phone number is invalid.
- 3 missing attendance values were filled with `0` because same-day practice questions were `0`.

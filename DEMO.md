# Demo Guide

Use this guide to present the working system in a live interview.

## 1. Run The Pipeline

Without Drive upload:

```bash
.venv/bin/python run_pipeline.py --as-of 2025-10-14
```

With Drive upload and Zapier trigger:

```bash
.venv/bin/python run_pipeline.py --as-of 2025-10-14 --upload-drive
```

Expected summary:

```text
Metadata rows loaded: 200
Students featured: 200
Students risk-scored: 200
Students queued for intervention: 58
Today actions: 54
Facilitator CSV folder: outputs/interventions/facilitators
```

## 2. Show Data Quality

Open:

```text
outputs/ingestion/quality_report.md
```

Talk track:

> The system is resilient to messy data. It validates schema, normalizes fields, imputes missing activity values using paired attendance/practice logic, and reports issues instead of silently hiding them.

## 3. Show Feature Table

Open:

```text
outputs/features/student_features_2025-10-14.csv
```

Highlight:

- `has_quiz`
- `quiz_count`
- `latest_quiz_score`
- `target_gap`
- `recent_sessions_attended`
- `recent_zero_attendance_days`
- `recent_practice_questions_avg`
- `notes_history`
- `days_until_next_quiz`

Talk track:

> Feature engineering here is not for an ML model yet. It turns raw operational rows into decision-ready signals for a transparent weighted score.

## 4. Show Risk Scores

Open:

```text
outputs/risk/student_risk_scores_2025-10-14.csv
```

Highlight:

- `risk_score`
- `risk_level`
- `risk_reasons`
- component risks and availability flags

Talk track:

> The risk score is a weighted average over available signals. If a quiz has not happened yet, quiz risk is skipped. If LLM notes are unavailable, notes are skipped. Missing is not treated as low risk.

## 5. Show Intervention Queue

Open:

```text
outputs/interventions/facilitator_action_queue_2025-10-14.csv
```

Highlight:

- `facilitator_email`
- `queue_rank`
- `today_action`
- `recommended_action`
- `message_draft`
- `action_plan_source`

Talk track:

> This is where the system becomes usable. Facilitators do not just get a score; they get who to contact, why, what to do, and a parent-ready Arabic message.

## 6. Show Per-Facilitator Files

Open:

```text
outputs/interventions/facilitators/
```

Talk track:

> The system writes one CSV per facilitator so Zapier does not need to split the data. Zapier only copies a template, inserts rows, and emails the link.

## 7. Show Google Sheet Template

Open:

```text
templates/facilitator_queue_template.xlsx
```

Highlight:

- risk score coloring
- risk level coloring
- status dropdown
- contact method dropdown
- outcome notes

Talk track:

> The facilitator Sheet is designed for action and feedback. Generated columns are for reading; status/outcome columns create the feedback loop.

## 8. Show Zapier Flow

Show the Zap:

```text
New facilitator CSV in Drive
  -> copy Sheet template
  -> insert CSV rows
  -> email facilitator link
```

Talk track:

> Zapier is not the intelligence layer. It is the workflow glue that gets outputs into tools facilitators already use: Google Sheets and email.

## 9. Feedback Loop

Explain the next Zap:

```text
Facilitator updates status
  -> Zapier appends row to intervention_log
  -> pipeline later ingests intervention_log
```

Talk track:

> The action queue solves today. The intervention log lets us learn tomorrow: intervention coverage, response rates, operational bottlenecks, and which actions improve attendance, practice, and quiz scores.

## 10. Tradeoffs

Current prototype:

- batch CSV pipeline
- Google Sheets delivery
- transparent weighted scoring
- LLM for notes and intervention language
- Zapier for distribution

Later engineering:

- scheduled hosted pipeline
- persistent database
- intervention log ingestion
- calibrated model after enough outcomes
- WhatsApp Business API integration


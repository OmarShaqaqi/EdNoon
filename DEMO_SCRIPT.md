# Demo Script

## 1. Start With The Story

Say:

> The goal is not only to predict risk. The goal is to make intervention happen before Quiz 2.

Show the architecture:

```text
pipeline -> facilitator sheets -> feedback webhook -> feedback analysis -> manager dashboard
```

## 2. Run The Main Pipeline

```bash
.venv/bin/python run_pipeline.py --as-of 2025-10-14
```

Show:

- `outputs/risk/student_risk_scores_2025-10-14.csv`
- `outputs/interventions/facilitator_action_queue_2025-10-14.csv`
- `outputs/interventions/facilitators/`

Say:

> This creates one prioritized action queue per facilitator.

## 3. Show A Facilitator Output

Open one facilitator CSV.

Point to:

- `risk_score`
- `risk_level`
- `recommended_action`
- `message_draft`
- `risk_reasons`
- `update_form_link`

Say:

> The facilitator does not need to inspect raw data. They get who to contact, why, and what to say.

## 4. Show The Feedback Path

Start the API:

```bash
.venv/bin/uvicorn api.main:app --reload --port 8000
```

Expose it for Zapier:

```bash
ngrok http 8000
```

In Zapier, POST to:

```text
https://YOUR-NGROK-URL.ngrok-free.app/intervention-log
```

Show:

```bash
cat data/intervention_log.csv
```

Say:

> This turns separate facilitator actions into one central feedback log.

## 5. Run Feedback Analysis

```bash
.venv/bin/python run_feedback.py --log-path data/intervention_log.csv
```

Show:

- `outputs/feedback/feedback_summary.csv`
- `outputs/feedback/feedback_by_facilitator.csv`
- `outputs/feedback/students_needing_followup.csv`

Say:

> Now we can measure intervention coverage and identify students still needing follow-up.

## 6. Open Manager Dashboard

```bash
.venv/bin/streamlit run dashboard/app.py
```

Show:

- top metrics
- campus risk load
- facilitator workload
- missing-intervention filter
- student detail table

Say:

> Facilitators act in Sheets. Managers monitor execution here.

## 7. Close With Tradeoffs

Say:

> For two days, I chose a batch pipeline, Sheets, Zapier, and Streamlit because they are fast and fit the users. At 100 campuses, I would move the same workflow onto a database, hosted API, scheduled jobs, auth, and audit logs.

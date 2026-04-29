# Feedback Layer

The feedback layer measures whether recommended interventions actually happened.

Your Google Form response sheet should be exported or synced as:

```text
data/intervention_log.csv
```

Expected columns:

- `student_id`
- `student_name`
- `facilitator_email`
- `risk_score`
- `recommended_action`
- `status`
- `contact_method`
- `outcome_notes`

Run:

```bash
.venv/bin/python run_feedback.py \
  --queue-path outputs/interventions/facilitator_action_queue_2025-10-14.csv \
  --log-path data/intervention_log.csv
```

Outputs:

- `outputs/feedback/feedback_summary.csv`
- `outputs/feedback/feedback_by_facilitator.csv`
- `outputs/feedback/feedback_by_status.csv`
- `outputs/feedback/students_needing_followup.csv`

What it measures:

- intervention coverage
- completion rate
- facilitator-level completion
- status distribution
- students still needing follow-up

This is how we prove whether the system moved intervention coverage from roughly `30%` toward `80%+`.


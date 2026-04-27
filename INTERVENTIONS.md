# Intervention Planning Layer

This layer converts risk scores into a facilitator-ready action queue.

Run:

```bash
.venv/bin/python run_interventions.py --risk-path outputs/risk/student_risk_scores_2025-10-14.csv
```

Outputs:

- `outputs/interventions/facilitator_action_queue_2025-10-14.csv`
- `outputs/interventions/facilitator_action_queue_2025-10-14.md`
- `outputs/interventions/facilitators/<facilitator>_facilitator_action_queue_2025-10-14.csv`

What it does:

- Filters out low-risk students marked as `monitor`.
- Converts risk level into an action priority:
  - `critical` -> `today`
  - `high` -> `within_48h`
  - `medium` -> `nudge_or_monitor`
  - `low` -> `monitor`
- Uses one LLM prompt to generate both `recommended_action` and `message_draft` from the risk context.
- Requires `message_draft` to be Arabic because parent communication is for an Arabic-speaking school context.
- Caps daily workload per facilitator using `max_daily_actions_per_facilitator`.
- Writes one CSV per facilitator so Zapier can send each facilitator only their own queue.
- Flags rows that need human review, such as invalid phone numbers or possible note/student mismatch.

The LLM prompt includes:

- student identity, grade, learning track, campus, facilitator, and phone validity
- target score, quiz score, previous quiz score, score delta, target gap, and days until next quiz
- recent attendance: observed days, attended sessions, zero-attendance days, average minutes, and attendance rate
- recent practice: average and total practice questions
- post-quiz behavior: attendance and practice since Quiz 1
- final risk score, risk level, risk reasons, and component risk values
- note-risk reason/signals, latest note, and full chronological notes timeline

If `OPENAI_API_KEY` or the `openai` package is unavailable, the layer falls back to deterministic action/message rules and records the source in `action_plan_source`.

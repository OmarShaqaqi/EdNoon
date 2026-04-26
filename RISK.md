# Risk Scoring Layer

This layer converts student features into a transparent weighted risk score from `0` to `100`.

Run:

```bash
.venv/bin/python run_risk.py --features-path outputs/features/student_features_2025-10-14.csv
```

Output:

- `outputs/risk/student_risk_scores_2025-10-14.csv`

The final score is a normalized weighted average over only the components that are available for that student:

```text
final_risk = sum(component_risk * weight where available)
           / sum(weight where available)
           * 100
```

Current components:

- `quiz_score_risk`, available only when `has_quiz = True`.
- `quiz_trend_risk`, available only when `quiz_count >= 2`.
- `attendance_risk`, available when recent activity rows exist.
- `practice_risk`, available when recent activity rows exist.
- `notes_risk`, available when facilitator notes exist and `OPENAI_API_KEY` is configured.
- `urgency_risk`, available when `days_until_next_quiz` is known.

This handles changing data naturally:

- Before any quiz, quiz score and quiz trend are skipped.
- After one quiz, quiz score is included but quiz trend is skipped.
- After more than one quiz, both quiz score and quiz trend are included.

Notes are analyzed by an LLM through the official OpenAI Python library and the Responses API. The model returns structured JSON:

- `risk`: note-only risk from `0` to `10`, normalized to `0-1` in code.
- `confidence`: model confidence from `0` to `10`, normalized to `0-1` in code.
- `reason`: concise explanation.
- `signals`: structured tags such as `attendance_issue`, `parent_unresponsive`, or `positive_momentum`.

Install dependencies if needed:

```bash
.venv/bin/pip install -r requirements.txt
```

If `OPENAI_API_KEY` is not configured, or the `openai` package is not installed, notes are skipped rather than scored with keyword rules. This keeps the rule-based risk engine honest: unavailable LLM analysis is treated as unavailable data, not as low risk.

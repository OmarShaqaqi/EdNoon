# Feature Engineering Layer

This layer turns cleaned operational tables into one row per student.

Run ingestion first:

```bash
.venv/bin/python run_ingestion.py
```

Then build features:

```bash
.venv/bin/python run_features.py --as-of 2025-10-14
```

Output:

- `outputs/features/student_features_2025-10-14.csv`

The table is intentionally model-agnostic. It can feed a transparent weighted risk score now and an ML model later once we collect labeled intervention outcomes.

Current feature groups:

- Student metadata: campus, facilitator, grade, target score, learning track.
- Quiz status: quiz count, whether any quiz exists, latest quiz score/date, previous quiz score, score delta, target gap, failed latest quiz.
- Recent activity: days observed, sessions actually attended, attendance average/rate, practice average/total, zero-attendance days.
- Post-Quiz-1 activity: observed days, attended sessions, attendance and practice since Quiz 1.
- Note activity: note count, latest note date/text, days since latest note, full chronological `notes_history`.

Quiz handling is intentionally simple:

- No quiz yet: `has_quiz = False`, `quiz_count = 0`, no failure is assigned, and target gap is `0`.
- One quiz: latest quiz fields are filled, previous score and score delta remain empty.
- More than one quiz: latest score, previous score, and `quiz_score_delta` are filled.

`days_until_next_quiz` is computed from configured quiz dates, not from the raw CSV column. The source column is shifted in the provided data before Quiz 1, so using the configured schedule is safer and more explainable.

Important distinction:

- `*_days_observed` counts rows we received data for.
- `*_sessions_attended` counts only days where `session_attended_min > 0`.
- `*_zero_attendance_days` counts days where a record exists but the student attended `0` minutes.

`notes_history` is designed for the next LLM step. Each note is formatted as:

```text
10-11: student note text...
10-14: follow-up note text...
```

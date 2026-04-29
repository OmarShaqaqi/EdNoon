# Manager Dashboard

This dashboard is a lightweight, read-only view for program or campus managers.

Facilitators still work from their Google Sheets. The dashboard is for monitoring:

- overall intervention coverage
- campus risk load
- facilitator workload
- high-risk students with no logged intervention
- student-level risk and recommended action context

Run it after the pipeline has produced outputs:

```bash
.venv/bin/streamlit run dashboard/app.py
```

The dashboard reads existing CSV outputs from:

- `outputs/risk/`
- `outputs/interventions/`
- `outputs/feedback/`

It does not write operational data or replace the Google Sheets workflow.

# Webhook API

This is a small FastAPI receiver for Zapier intervention feedback events.

The normal facilitator workflow can still use Google Forms. This API is useful when you want Zapier to push each submitted intervention directly into the project.

## Run Locally

```bash
.venv/bin/uvicorn api.main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

Send a test event:

```bash
curl -X POST http://localhost:8000/intervention-log \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "S084",
    "student_name": "Amal Al-Subai",
    "facilitator_email": "facilitator4@noon.com",
    "risk_score": 73.1,
    "recommended_action": "Call parent today to diagnose attendance barrier",
    "status": "called_parent",
    "contact_method": "phone_call",
    "outcome_notes": "Parent answered and agreed to monitor practice tonight."
  }'
```

By default, events are appended to:

```text
data/intervention_log.csv
```

The feedback layer can already read that file:

```bash
.venv/bin/python run_feedback.py --log-path data/intervention_log.csv
```

## Zapier Setup

1. Trigger: new Google Form response.
2. Action: Webhooks by Zapier -> POST.
3. URL: your webhook URL, for example `https://YOUR-NGROK-URL.ngrok-free.app/intervention-log`.
4. Payload Type: JSON.
5. Map form fields to:
   - `student_id`
   - `student_name`
   - `facilitator_email`
   - `risk_score`
   - `recommended_action`
   - `status`
   - `contact_method`
   - `outcome_notes`

## Optional Security

Set this in `.env`:

```text
WEBHOOK_API_KEY=some-random-secret
```

Then add this header in Zapier:

```text
X-Webhook-Key: some-random-secret
```

For production, deploy this API to a cloud service instead of running it through ngrok on a laptop.

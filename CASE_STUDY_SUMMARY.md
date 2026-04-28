# Boon Academy Intervention System

## Goal

Boon has six days before Quiz 2. Only about 30% of students who fail quizzes currently receive intervention before the next quiz. The goal is to raise intervention coverage to 80%+ without overwhelming facilitators.

## Diagnosis

The problem is mainly an execution workflow problem:

- facilitators do not have a prioritized student list
- attendance, practice, quiz, and notes data are scattered
- free-text notes are hard to scan quickly
- facilitators need recommended actions, not only risk scores
- managers cannot easily see who has not been contacted
- feedback is not captured in a way that improves the system

## What I Built

I built a lightweight intervention operating system:

```text
Raw CSVs
-> ingestion and cleaning
-> student features
-> weighted risk scoring
-> LLM note/action support
-> facilitator action queues
-> Google Drive + Zapier delivery
-> Google Form / webhook feedback
-> feedback analytics
-> manager dashboard
```

Facilitators work from Google Sheets and WhatsApp. Managers monitor execution from a Streamlit dashboard.

## Risk Scoring

Risk is a weighted average over available signals:

- quiz performance
- quiz trend
- attendance
- practice
- facilitator notes
- urgency before next quiz

If a signal is unavailable, its weight is skipped instead of treating missing data as low risk. Before any quiz, the system uses attendance, practice, notes, and urgency. After one quiz, it adds quiz performance. After multiple quizzes, it adds quiz trend.

## AI Usage

The LLM is used only where language judgment helps:

- analyzing facilitator notes into note risk, confidence, reason, and signals
- generating a recommended action and Arabic parent message draft

Numeric cleaning, feature calculation, and weighted risk scoring stay deterministic and explainable.

## Facilitator Workflow

Each facilitator receives a focused queue with:

- student name and parent phone
- risk score and risk level
- action priority
- recommended action
- Arabic message draft
- risk reasons
- prefilled update form link

The Sheet is for action. The form captures feedback.

## Feedback Loop

When a facilitator submits an update:

```text
Google Form
-> Zapier
-> FastAPI webhook
-> data/intervention_log.csv
-> feedback analysis
-> dashboard update
```

This measures coverage, follow-up needs, facilitator workload, response rates, and later action effectiveness.

## Tradeoffs

Fast prototype choices:

- CSV outputs instead of database
- rule-based risk instead of ML
- Google Sheets instead of a custom facilitator app
- Zapier instead of a custom workflow engine
- local/ngrok API for demo webhook
- Streamlit for manager dashboard

These choices are pragmatic for a two-day prototype. At 100 campuses, I would move to a cloud database, hosted API, scheduled jobs, authentication, audit logs, and a stronger evaluation pipeline.

## Rollout Plan

Day 1-2:

- deploy for 20 campuses
- generate and send facilitator queues
- enable feedback capture
- give managers dashboard visibility

Day 2-6:

- run the pipeline daily
- monitor coverage and follow-up
- escalate high-risk students with no action
- tune thresholds based on facilitator load

Week 2:

- compare Quiz 2 results with intervention logs
- measure coverage improvement
- review which actions correlated with recovery

Month 2:

- migrate from CSVs to database
- deploy API to cloud
- add auth and audit logs
- automate daily runs
- scale to 100 campuses

## Final Takeaway

This is not just a risk model. It is an intervention execution system: it identifies who needs help, explains why, recommends what to do, tracks whether action happened, and gives managers visibility before students fall through the cracks.

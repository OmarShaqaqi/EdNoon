from __future__ import annotations

import re

import pandas as pd

from .quality import QualityReport


def clean_student_metadata(df: pd.DataFrame, report: QualityReport) -> pd.DataFrame:
    dataset = "student_metadata"
    cleaned = df.copy()

    cleaned["student_id"] = normalize_id(cleaned["student_id"])
    cleaned["student_name"] = cleaned["student_name"].fillna("").astype(str).str.strip()
    cleaned["campus_id"] = cleaned["campus_id"].fillna("").astype(str).str.strip().str.upper()
    cleaned["facilitator_email"] = normalize_email(cleaned["facilitator_email"])
    cleaned["learning_track"] = cleaned["learning_track"].fillna("Unknown").astype(str).str.strip()

    cleaned["grade"] = pd.to_numeric(cleaned["grade"], errors="coerce")
    report.warn(dataset, "missing_or_invalid_grade", cleaned["grade"].isna().sum())
    cleaned["grade"] = cleaned["grade"].fillna(0).astype(int)

    cleaned["target_score"] = pd.to_numeric(cleaned["target_score"], errors="coerce")
    report.warn(dataset, "missing_target_score_defaulted_to_70", cleaned["target_score"].isna().sum())
    report.warn(
        dataset,
        "suspicious_target_score_outside_0_to_100",
        cleaned["target_score"].notna().where(cleaned["target_score"].between(0, 100), False).eq(False).sum(),
        "Kept after clipping to 0-100;",
    )
    cleaned["target_score"] = cleaned["target_score"].fillna(70).clip(0, 100).astype(int)

    phone_info = cleaned["parent_phone"].map(normalize_saudi_phone)
    cleaned["parent_phone"] = phone_info.map(lambda item: item[0])
    cleaned["parent_phone_valid"] = phone_info.map(lambda item: item[1])
    report.warn(dataset, "invalid_parent_phone", (~cleaned["parent_phone_valid"]).sum())

    duplicate_ids = cleaned.duplicated(subset=["student_id"], keep="last")
    report.warn(dataset, "duplicate_student_id_rows_dropped", duplicate_ids.sum())
    cleaned = cleaned[~duplicate_ids].copy()

    missing_ids = cleaned["student_id"].eq("")
    report.error(dataset, "missing_student_id_rows_dropped", missing_ids.sum())
    cleaned = cleaned[~missing_ids].copy()

    return cleaned.reset_index(drop=True)


def clean_daily_metrics(
    df: pd.DataFrame, known_student_ids: set[str], report: QualityReport
) -> pd.DataFrame:
    dataset = "student_daily_metrics"
    cleaned = df.copy()

    cleaned["student_id"] = normalize_id(cleaned["student_id"])
    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")
    report.error(dataset, "invalid_date_rows_dropped", cleaned["date"].isna().sum())
    cleaned = cleaned[cleaned["date"].notna()].copy()

    cleaned["session_attended_min"] = pd.to_numeric(cleaned["session_attended_min"], errors="coerce")
    report.warn(dataset, "session_attended_min_clipped_to_0_90", (~cleaned["session_attended_min"].between(0, 90) & cleaned["session_attended_min"].notna()).sum())
    cleaned["session_attended_min"] = cleaned["session_attended_min"].clip(0, 90)

    cleaned["practice_questions"] = pd.to_numeric(cleaned["practice_questions"], errors="coerce")
    report.warn(dataset, "practice_questions_clipped_to_0_250", (~cleaned["practice_questions"].between(0, 250) & cleaned["practice_questions"].notna()).sum())
    cleaned["practice_questions"] = cleaned["practice_questions"].clip(0, 250)
    cleaned = impute_activity_pair(cleaned, report)
    cleaned["practice_questions"] = cleaned["practice_questions"].round().astype(int)

    cleaned["last_quiz_score"] = pd.to_numeric(cleaned["last_quiz_score"], errors="coerce")
    report.warn(dataset, "quiz_score_clipped_to_0_100", (~cleaned["last_quiz_score"].between(0, 100) & cleaned["last_quiz_score"].notna()).sum())
    cleaned["last_quiz_score"] = cleaned["last_quiz_score"].clip(0, 100)

    cleaned["days_until_next_quiz"] = pd.to_numeric(cleaned["days_until_next_quiz"], errors="coerce")
    report.warn(dataset, "missing_days_until_next_quiz", cleaned["days_until_next_quiz"].isna().sum())

    unknown_students = ~cleaned["student_id"].isin(known_student_ids)
    report.error(dataset, "unknown_student_id_rows_quarantined", unknown_students.sum())
    cleaned = cleaned[~unknown_students].copy()

    duplicates = cleaned.duplicated(subset=["student_id", "date"], keep="last")
    report.warn(dataset, "duplicate_student_date_rows_dropped", duplicates.sum())
    cleaned = cleaned[~duplicates].copy()

    return cleaned.sort_values(["student_id", "date"]).reset_index(drop=True)


def clean_facilitator_notes(
    df: pd.DataFrame, known_student_ids: set[str], report: QualityReport
) -> pd.DataFrame:
    dataset = "facilitator_notes"
    cleaned = df.copy()

    cleaned["note_id"] = cleaned["note_id"].fillna("").astype(str).str.strip()
    cleaned["student_id"] = normalize_id(cleaned["student_id"])
    cleaned["facilitator_email"] = normalize_email(cleaned["facilitator_email"])
    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce")
    cleaned["note_text"] = cleaned["note_text"].fillna("").astype(str).str.strip()

    report.error(dataset, "invalid_date_rows_dropped", cleaned["date"].isna().sum())
    cleaned = cleaned[cleaned["date"].notna()].copy()

    unknown_students = ~cleaned["student_id"].isin(known_student_ids)
    report.error(dataset, "unknown_student_id_rows_quarantined", unknown_students.sum())
    cleaned = cleaned[~unknown_students].copy()

    empty_notes = cleaned["note_text"].eq("")
    report.warn(dataset, "empty_note_text_rows_dropped", empty_notes.sum())
    cleaned = cleaned[~empty_notes].copy()

    duplicates = cleaned.duplicated(subset=["note_id"], keep="last") & cleaned["note_id"].ne("")
    report.warn(dataset, "duplicate_note_id_rows_dropped", duplicates.sum())
    cleaned = cleaned[~duplicates].copy()

    return cleaned.sort_values(["student_id", "date", "note_id"]).reset_index(drop=True)


def normalize_id(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().str.upper()


def impute_activity_pair(df: pd.DataFrame, report: QualityReport) -> pd.DataFrame:
    dataset = "student_daily_metrics"
    cleaned = df.copy()

    student_session_avg = cleaned.groupby("student_id")["session_attended_min"].transform("mean")
    student_practice_avg = cleaned.groupby("student_id")["practice_questions"].transform("mean")

    missing_session = cleaned["session_attended_min"].isna()
    missing_practice = cleaned["practice_questions"].isna()

    session_zero_fill = missing_session & cleaned["practice_questions"].fillna(0).eq(0)
    session_avg_fill = missing_session & cleaned["practice_questions"].fillna(0).ne(0)
    practice_zero_fill = missing_practice & cleaned["session_attended_min"].fillna(0).eq(0)
    practice_avg_fill = missing_practice & cleaned["session_attended_min"].fillna(0).ne(0)

    cleaned.loc[session_zero_fill, "session_attended_min"] = 0
    cleaned.loc[session_avg_fill, "session_attended_min"] = student_session_avg[session_avg_fill]
    cleaned.loc[practice_zero_fill, "practice_questions"] = 0
    cleaned.loc[practice_avg_fill, "practice_questions"] = student_practice_avg[practice_avg_fill]

    unresolved_session = cleaned["session_attended_min"].isna()
    unresolved_practice = cleaned["practice_questions"].isna()
    cleaned.loc[unresolved_session, "session_attended_min"] = 0
    cleaned.loc[unresolved_practice, "practice_questions"] = 0

    report.warn(dataset, "missing_session_attended_min_filled_with_zero_when_practice_zero", session_zero_fill.sum())
    report.warn(dataset, "missing_session_attended_min_filled_with_student_average", session_avg_fill.sum())
    report.warn(dataset, "missing_practice_questions_filled_with_zero_when_session_zero", practice_zero_fill.sum())
    report.warn(dataset, "missing_practice_questions_filled_with_student_average", practice_avg_fill.sum())
    report.warn(dataset, "missing_session_attended_min_no_student_average_defaulted_to_0", unresolved_session.sum())
    report.warn(dataset, "missing_practice_questions_no_student_average_defaulted_to_0", unresolved_practice.sum())
    return cleaned


def normalize_email(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().str.lower()


def normalize_saudi_phone(raw: object) -> tuple[str, bool]:
    digits = re.sub(r"\D", "", str(raw or ""))
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("966") and len(digits) == 12:
        return f"+{digits}", True
    if digits.startswith("05") and len(digits) == 10:
        return f"+966{digits[1:]}", True
    if digits.startswith("5") and len(digits) == 9:
        return f"+966{digits}", True
    return (f"+{digits}" if digits else "", False)

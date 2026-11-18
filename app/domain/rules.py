"""Declarative rule catalog and vectorized, deterministic evaluations."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from app.core.config import Settings


@dataclass(frozen=True)
class Rule:
    code: str
    category: str
    severity: str
    description: str
    field: str
    entity: str = "transaction"

    @property
    def suggested_action(self) -> str:
        return f"Verify {self.field} against the synthetic source and correct the record; rerun validation."


RULES = [
    Rule("DQ001", "Completeness", "High", "Transaction ID is required", "transaction_id"),
    Rule("DQ002", "Completeness", "High", "Account ID is required", "account_id"),
    Rule("DQ003", "Completeness", "High", "Transaction date is required", "transaction_date"),
    Rule("DQ004", "Completeness", "High", "Amount is required", "amount"),
    Rule("DQ005", "Completeness", "Medium", "Currency is required", "currency"),
    Rule("DQ006", "Completeness", "High", "Business unit is required", "business_unit_id"),
    Rule("DQ010", "Validity", "High", "Amount must be finite numeric", "amount"),
    Rule("DQ011", "Validity", "High", "Amount cannot be negative", "amount"),
    Rule("DQ012", "Validity", "Medium", "Currency must be a reference value", "currency"),
    Rule(
        "DQ013",
        "Validity",
        "Medium",
        "Transaction type must be a reference value",
        "transaction_type",
    ),
    Rule("DQ014", "Validity", "Medium", "Status must be a reference value", "status"),
    Rule("DQ015", "Validity", "Low", "Priority must be a reference value", "priority"),
    Rule("DQ016", "Validity", "High", "Business unit must exist", "business_unit_id"),
    Rule("DQ017", "Validity", "High", "Transaction date must be ISO datetime", "transaction_date"),
    Rule("DQ018", "Validity", "High", "Processing date must be ISO datetime", "processing_date"),
    Rule(
        "DQ019",
        "Consistency",
        "High",
        "Completed records need a processing date",
        "processing_date",
    ),
    Rule(
        "DQ020",
        "Consistency",
        "High",
        "Processing date precedes transaction date beyond tolerance",
        "processing_date",
    ),
    Rule(
        "DQ021",
        "Consistency",
        "High",
        "Resolved/closed exceptions require a valid resolution time",
        "resolved_at",
        "exception",
    ),
    Rule(
        "DQ022",
        "Consistency",
        "High",
        "Completed actions require a valid completion time",
        "completed_at",
        "action",
    ),
    Rule(
        "DQ023",
        "Governance",
        "High",
        "High/critical exceptions require an owner",
        "owner",
        "exception",
    ),
    Rule(
        "DQ030",
        "Duplicate",
        "High",
        "Transaction ID is duplicated within dataset",
        "transaction_id",
    ),
    Rule("DQ040", "Timeliness", "High", "Processing turnaround is negative", "processing_date"),
    Rule(
        "DQ041",
        "Timeliness",
        "High",
        "Processing or open age exceeds configured SLA",
        "processing_date",
    ),
    Rule(
        "DQ050",
        "Referential Integrity",
        "Critical",
        "Account reference does not exist",
        "account_id",
    ),
    Rule("DQ051", "Referential Integrity", "High", "Team reference does not exist", "team_id"),
    Rule(
        "DQ052",
        "Referential Integrity",
        "High",
        "Source system reference does not exist",
        "source_system_id",
    ),
    Rule("DQ060", "Outlier", "Medium", "Amount exceeds project high-value threshold", "amount"),
]
ROOT_CAUSES = {
    "Completeness": "Missing upstream data",
    "Validity": "Invalid source value",
    "Consistency": "Business-rule violation",
    "Duplicate": "Duplicate submission",
    "Timeliness": "Processing delay",
    "Referential Integrity": "Reference-data mismatch",
    "Outlier": "Business-rule violation",
    "Governance": "System integration issue",
}


def missing(series: pd.Series) -> pd.Series:
    return series.isna() | series.astype(str).str.strip().eq("")


def evaluate_rules(
    frame: pd.DataFrame,
    refs: dict[str, set[str]],
    policy: "Settings",
    as_of: str,
    entity: str = "transaction",
) -> dict[str, pd.Series]:
    masks: dict[str, pd.Series] = {}
    if frame.empty:
        return masks
    f = frame.copy()
    for rule in RULES:
        if rule.entity == entity and rule.field not in f:
            f[rule.field] = None
    if entity == "transaction":
        amount = pd.to_numeric(f.amount, errors="coerce")
        start = pd.to_datetime(f.transaction_date, errors="coerce", utc=True, format="ISO8601")
        end = pd.to_datetime(f.processing_date, errors="coerce", utc=True, format="ISO8601")
        tat = (end - start).dt.total_seconds() / 3600
        pending_age = (pd.Timestamp(as_of, tz="UTC") - start).dt.total_seconds() / 3600
        for rule in RULES:
            if rule.entity != entity:
                continue
            col = f[rule.field]
            code = rule.code
            if rule.category == "Completeness":
                mask = missing(col)
            elif code == "DQ010":
                mask = ~missing(col) & (amount.isna() | ~np.isfinite(amount))
            elif code == "DQ011":
                mask = amount.lt(0)
            elif code in {"DQ012", "DQ013", "DQ014", "DQ015", "DQ016", "DQ050", "DQ051", "DQ052"}:
                mask = ~missing(col) & ~col.isin(refs[rule.field])
                # Team/source IDs are operationally mandatory even without a completeness rule.
                if code in {"DQ013", "DQ014", "DQ015", "DQ051", "DQ052"}:
                    mask |= missing(col)
            elif code in {"DQ017", "DQ018"}:
                dates = start if code == "DQ017" else end
                mask = ~missing(col) & dates.isna()
            elif code == "DQ019":
                mask = f.status.eq("Completed") & missing(col)
            elif code == "DQ020":
                mask = tat.lt(-policy.date_tolerance_minutes / 60)
            elif code == "DQ030":
                mask = ~missing(col) & col.duplicated(keep="first")
            elif code == "DQ040":
                mask = tat.lt(0)
            elif code == "DQ041":
                mask = (f.status.eq("Completed") & tat.gt(policy.sla_hours)) | (
                    ~f.status.eq("Completed") & pending_age.gt(policy.sla_hours)
                )
            elif code == "DQ060":
                mask = amount.gt(policy.high_value_threshold) & np.isfinite(amount)
            else:
                continue
            masks[code] = mask.fillna(False)
    else:
        for rule in RULES:
            if rule.entity != entity:
                continue
            if rule.code in {"DQ021", "DQ022"}:
                states = ["Resolved", "Closed"] if entity == "exception" else ["Completed"]
                invalid = pd.to_datetime(
                    f[rule.field], errors="coerce", utc=True, format="ISO8601"
                ).isna()
                masks[rule.code] = f.status.isin(states) & invalid
            elif rule.code == "DQ023":
                masks[rule.code] = f.severity.isin(["Critical", "High"]) & missing(f.owner)
    return {code: mask for code, mask in masks.items() if code not in policy.disabled_rules}

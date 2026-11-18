"""Validated configuration; no credentials or remote dependencies."""

import json
import os
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    database_url: str = "sqlite:///data/finops.db"
    output_dir: Path = Path("reports")
    sla_hours: float = Field(default=48, gt=0)
    date_tolerance_minutes: float = Field(default=0, ge=0)
    high_value_threshold: float = Field(default=1_000_000, gt=0)
    weights: dict[str, float] = Field(
        default_factory=lambda: {
            "completeness": 0.3,
            "validity": 0.3,
            "consistency": 0.2,
            "timeliness": 0.2,
        }
    )
    aging_days: list[int] = Field(default_factory=lambda: [2, 7, 14, 30])
    disabled_rules: list[str] = Field(default_factory=list)
    severity_overrides: dict[str, str] = Field(default_factory=dict)
    priority_age_days: int = Field(default=7, ge=0)
    high_risk_score: int = Field(default=12, ge=1, le=25)

    @model_validator(mode="after")
    def valid_policy(self) -> "Settings":
        if set(self.weights) != {"completeness", "validity", "consistency", "timeliness"}:
            raise ValueError("weights must contain the four documented quality dimensions")
        if any(v < 0 for v in self.weights.values()) or abs(sum(self.weights.values()) - 1) > 1e-6:
            raise ValueError("weights must be nonnegative and sum to 1")
        if (
            not self.aging_days
            or sorted(set(self.aging_days)) != self.aging_days
            or self.aging_days[0] < 0
        ):
            raise ValueError("aging_days must be strictly increasing nonnegative boundaries")
        if any(
            v not in {"Low", "Medium", "High", "Critical"} for v in self.severity_overrides.values()
        ):
            raise ValueError("unknown severity override")
        from app.domain.rules import RULES

        codes = {r.code for r in RULES}
        if (set(self.disabled_rules) | set(self.severity_overrides)) - codes:
            raise ValueError("unknown validation rule code in policy")
        return self


def get_settings() -> Settings:
    path = Path(os.environ.get("FINOPS_CONFIG", "config/policy.json"))
    values = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if "FINOPS_DATABASE_URL" in os.environ:
        values["database_url"] = os.environ["FINOPS_DATABASE_URL"]
    if "FINOPS_OUTPUT_DIR" in os.environ:
        values["output_dir"] = os.environ["FINOPS_OUTPUT_DIR"]
    return Settings(**values)

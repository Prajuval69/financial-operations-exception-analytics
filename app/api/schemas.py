from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Priority = Literal["P1", "P2", "P3", "P4"]
ExceptionStatus = Literal["Detected", "Assigned", "In Progress", "Resolved", "Closed", "Reopened"]
ActionStatus = Literal["Open", "In Progress", "Blocked", "Completed", "Cancelled"]
RiskStatus = Literal["Open", "Mitigating", "Closed"]


class InputModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("owner", "title", check_fields=False)
    @classmethod
    def nonblank(cls, value):
        if value is not None and not value.strip():
            raise ValueError("Value cannot be blank")
        return value


class ExceptionPatch(InputModel):
    owner: str | None = Field(default=None, max_length=100)
    status: ExceptionStatus | None = None
    priority: Priority | None = None
    resolution_notes: str | None = Field(default=None, max_length=4000)


class ActionCreate(InputModel):
    exception_id: int | None = Field(default=None, gt=0)
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    owner: str = Field(min_length=1, max_length=100)
    priority: Priority = "P2"
    due_date: datetime
    dependency: int | None = Field(default=None, gt=0)


class ActionPatch(InputModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    owner: str | None = Field(default=None, min_length=1, max_length=100)
    priority: Priority | None = None
    due_date: datetime | None = None
    dependency: int | None = Field(default=None, gt=0)
    status: ActionStatus | None = None


class RiskCreate(InputModel):
    related_exception_id: int | None = Field(default=None, gt=0)
    action_id: int | None = Field(default=None, gt=0)
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    probability: int = Field(ge=1, le=5, strict=True)
    impact: int = Field(ge=1, le=5, strict=True)
    owner: str = Field(min_length=1, max_length=100)
    mitigation: str = Field(default="", max_length=4000)
    due_date: datetime


class RiskPatch(InputModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    owner: str | None = Field(default=None, min_length=1, max_length=100)
    mitigation: str | None = Field(default=None, max_length=4000)
    due_date: datetime | None = None
    probability: int | None = Field(default=None, ge=1, le=5, strict=True)
    impact: int | None = Field(default=None, ge=1, le=5, strict=True)
    status: RiskStatus | None = None
    action_id: int | None = Field(default=None, gt=0)


class ValidationInput(InputModel):
    as_of: datetime | None = None

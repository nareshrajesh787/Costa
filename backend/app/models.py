"""Pydantic request/response models."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.lib.constants import SUBMITTER_TYPES, VOLUME_SEVERITY


Volume = Literal["small", "medium", "large"]
Submitter = Literal["resident", "fisher", "hotel_staff", "lifeguard", "municipal_scout"]
Horizon = Literal["h12", "h24", "h48"]
Role = Literal["citizen", "operations"]


class ReportIn(BaseModel):
    zoneId: str
    volume: Volume
    submitterType: Submitter
    note: str = ""

    @field_validator("note")
    @classmethod
    def cap_note(cls, value: str) -> str:
        return value.strip()[:280]


class InspectionIn(BaseModel):
    zoneId: str
    observedVolume: Volume
    note: str = ""


class SettingsIn(BaseModel):
    crewBudget: int | None = Field(default=None, ge=4, le=16)
    explorationC: float | None = Field(default=None, ge=0.1, le=2.0)
    forecastWeight: float | None = Field(default=None, ge=0.0, le=1.0)
    horizon: Horizon | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    region: str | None = None


class ZoneEconomicsIn(BaseModel):
    zoneId: str
    economicWeight: float | None = Field(default=None, ge=0.1, le=5)
    hourlyRevenueAtRisk: float | None = Field(default=None, ge=0)
    cleanupCostPerHour: float | None = Field(default=None, ge=0)
    requiredCrewHours: int | None = Field(default=None, ge=1, le=8)


class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=120)
    password: str = Field(min_length=8, max_length=120)
    municipality: str = Field(min_length=2, max_length=80)
    region: str = ""
    role: Role = "citizen"
    lat: float = Field(default=18.3256, ge=-90, le=90)
    lng: float = Field(default=-65.6524, ge=-180, le=180)

    @field_validator("email")
    @classmethod
    def email_format(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if "@" not in cleaned or "." not in cleaned.split("@")[-1]:
            raise ValueError("Enter a valid email")
        return cleaned

    @field_validator("name", "municipality", "region")
    @classmethod
    def strip_text(cls, value: str) -> str:
        return value.strip()


class LoginIn(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def lower_email(cls, value: str) -> str:
        return value.strip().lower()


class ExplainIn(BaseModel):
    summaryContext: dict[str, Any] | None = None


class AskIn(BaseModel):
    question: str = Field(min_length=4, max_length=280)
    summaryContext: dict[str, Any] | None = None

    @field_validator("question")
    @classmethod
    def strip_question(cls, value: str) -> str:
        return value.strip()


class DemoPlayIn(BaseModel):
    eventId: str = "cove-surge"


# Re-export for validation helpers
ALLOWED_VOLUMES = set(VOLUME_SEVERITY)
ALLOWED_SUBMITTERS = set(SUBMITTER_TYPES)

from __future__ import annotations
from enum import Enum

from pydantic import BaseModel


class Status(str, Enum):
    RESULT = "result"
    UNDECLARED = "undeclared"


class CandidateResult(BaseModel):
    party_code: str
    candidate: str
    vote_number: int | None
    vote_share: float | None
    is_previous_mp: bool


class ConstituencyBase(BaseModel):
    constituency_id: str
    name: str
    region: str
    country: str
    result_2019: str
    majority_2019_percent: float
    status: Status
    time_reported: int | None
    time_declared: int | None
    result_2024: str | None
    majority_2024_number: int | None
    majority_2024_percent: float | None
    turnout_2024_number: int | None
    turnout_2024_percent: float | None


class ConstituencyOverview(ConstituencyBase):
    pass


class ConstituencyDetail(ConstituencyBase, CandidateResult):
    pass

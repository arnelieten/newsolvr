from typing import Literal

from pydantic import BaseModel, field_validator


INDUSTRY_LITERAL = Literal[
    "healthcare",
    "technology",
    "manufacturing",
    "financial_services",
    "education",
    "energy",
    "government",
    "other",
]


class ProblemReport(BaseModel):
    """Matches problem_analyzer.md: summary + detailed statement + 13 scores (0–5) + problem_size + industry."""

    problem_summary: str
    problem_statement: str
    meaningful_problem: int
    pain_intensity: int
    frequency: int
    problem_size: Literal["niche", "global"]
    industry: INDUSTRY_LITERAL
    market_growth: int
    willingness_to_pay: int
    target_customer_clarity: int
    problem_awareness: int
    differentiation_potential: int
    software_solution: int
    ai_fit: int
    speed_to_mvp: int
    business_potential: int
    time_relevancy: int

    @field_validator("problem_size", mode="before")
    @classmethod
    def normalize_problem_size(cls, v: object) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("industry", mode="before")
    @classmethod
    def normalize_industry(cls, v: object) -> str:
        if isinstance(v, str):
            return v.strip().lower().replace(" ", "_")
        return v


SCORE_COLUMNS = [
    "meaningful_problem",
    "pain_intensity",
    "frequency",
    "problem_size",
    "market_growth",
    "willingness_to_pay",
    "target_customer_clarity",
    "problem_awareness",
    "competition",
    "software_solution",
    "ai_fit",
    "speed_to_mvp",
    "business_potential",
    "time_relevancy",
]

# Columns used only for numeric scoring (excludes categorical problem_size).
NUMERIC_SCORE_COLUMNS = [
    c for c in SCORE_COLUMNS if c != "problem_size"
]

from pydantic import BaseModel


class ProblemReport(BaseModel):
    """Matches problem_analyzer.md: one summary + 14 scores (1–5)."""

    problem_statement: str
    meaningful_problem: int
    pain_intensity: int
    frequency: int
    problem_size: int
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

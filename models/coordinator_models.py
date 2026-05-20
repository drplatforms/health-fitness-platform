from pydantic import BaseModel


class UnifiedHealthReport(BaseModel):
    overall_score: int
    biggest_issue: str
    likely_cause: str
    priority_action: str
    recommendation: str

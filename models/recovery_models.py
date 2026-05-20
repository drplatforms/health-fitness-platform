from pydantic import BaseModel


class RecoveryAssessment(BaseModel):
    recovery_score: int
    training_readiness: str
    priority_action: str
    recommendation: str

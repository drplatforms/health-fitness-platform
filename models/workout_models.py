from pydantic import BaseModel


class WorkoutAssessment(BaseModel):

    workout_score: int

    training_balance: str

    recovery_risk: str

    progression_status: str

    recommendation: str
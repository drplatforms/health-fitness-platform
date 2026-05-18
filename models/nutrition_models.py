from pydantic import BaseModel


class NutritionAssessment(BaseModel):
    nutrition_score: int
    protein_status: str
    calorie_status: str
    recovery_impact: str
    recommendation: str
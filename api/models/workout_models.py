# =====================================
# Imports
# =====================================

from pydantic import BaseModel

from typing import List
from typing import Optional

# =====================================
# Workout Set Request Model
# =====================================


class WorkoutSetRequest(BaseModel):

    exercise_id: int

    set_number: int

    reps: int

    weight: float

    rir: Optional[int] = None


# =====================================
# Workout Request Model
# =====================================


class WorkoutRequest(BaseModel):

    user_id: int

    workout_name: str

    duration_minutes: int

    notes: Optional[str] = None

    sets: List[WorkoutSetRequest]

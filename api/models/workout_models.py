# =====================================
# Imports
# =====================================


from pydantic import BaseModel

# =====================================
# Workout Set Request Model
# =====================================


class WorkoutSetRequest(BaseModel):
    exercise_id: int

    set_number: int

    reps: int

    weight: float

    rir: int | None = None


# =====================================
# Workout Request Model
# =====================================


class WorkoutRequest(BaseModel):
    user_id: int

    workout_name: str

    duration_minutes: int

    notes: str | None = None

    sets: list[WorkoutSetRequest]

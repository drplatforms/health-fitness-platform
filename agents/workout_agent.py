from dotenv import load_dotenv

from crewai import Agent, Task, Crew, LLM

from services.workout_service import get_recent_workouts
from services.user_service import get_user_profile

from models.workout_models import WorkoutAssessment

load_dotenv()
# -----------------------------
# Select User
# -----------------------------

user_id = int(input("User ID: "))

user_profile = get_user_profile(user_id)

workouts = get_recent_workouts(user_id)


# -----------------------------
# Validate Data
# -----------------------------

if not workouts:
    print("No workout data found.")
    exit()


# -----------------------------
# Build Workout Summary
# -----------------------------

workout_summary = ""

for workout in workouts:
    session = workout["session"]

    workout_summary += (
        f"\nWorkout: {session['workout_name']}\n"
        f"Date: {session['workout_date']}\n"
        f"Duration: {session['duration_minutes']} minutes\n"
    )

    for set_data in workout["sets"]:
        workout_summary += (
            f"- {set_data['name']} | {set_data['reps']} reps x {set_data['weight']} lbs"
        )

        if set_data["rir"] is not None:
            workout_summary += f" | RIR {set_data['rir']}"

        workout_summary += "\n"


# -----------------------------
# Local LLM
# -----------------------------

fast_llm = LLM(model="ollama/qwen3:8b", base_url="http://localhost:11434")

llm = fast_llm


# -----------------------------
# Workout Agent
# -----------------------------

workout_agent = Agent(
    role="Strength and Conditioning Coach",
    goal="""
    Analyze workout performance,
    recovery demand,
    progression,
    and training balance.
    """,
    backstory="""
    You specialize in resistance training,
    progression analysis,
    fatigue management,
    and performance optimization.
    """,
    llm=llm,
    verbose=True,
    response_format=WorkoutAssessment,
)


# -----------------------------
# Workout Task
# -----------------------------

workout_task = Task(
    description=f"""
    Analyze the following user profile
    and workout history.

    User Profile:
    Name: {user_profile["name"]}
    Gender: {user_profile["gender"]}
    Age: {user_profile["age"]}
    Height: {user_profile["height_cm"]} cm
    Starting Weight: {user_profile["starting_weight"]}
    Goal Weight: {user_profile["goal_weight"]}
    Primary Goal: {user_profile["primary_goal"]}
    Activity Level: {user_profile["activity_level"]}

    Workout History:
    {workout_summary}

    Analyze:
    1. Training balance
    2. Recovery demand
    3. Progression quality
    4. Potential overtraining risk
    5. Overall workout quality

    Return your response in this exact structure:

    {{
        "workout_score": integer from 1-10,
        "training_balance": "poor/moderate/good",
        "recovery_risk": "low/moderate/high",
        "progression_status": "poor/moderate/good",
        "recommendation": "concise recommendation"
    }}
    """,
    expected_output="""
    Structured workout assessment.
    """,
    agent=workout_agent,
)


# -----------------------------
# Build Crew
# -----------------------------

crew = Crew(agents=[workout_agent], tasks=[workout_task], verbose=True)


# -----------------------------
# Run Workflow
# -----------------------------

result = crew.kickoff()

print("\n=== WORKOUT REPORT ===\n")
print(result)

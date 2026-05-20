from dotenv import load_dotenv

from crewai import Agent, Task, Crew, LLM

from services.recovery_service import get_recent_recovery_metrics
from services.nutrition_service import get_nutrition_analysis
from services.workout_service import get_recent_workouts
from services.user_service import get_user_profile
from services.report_service import save_health_report

load_dotenv()


def generate_health_report(user_id):
    user_profile = get_user_profile(user_id)

    recovery_data = get_recent_recovery_metrics()

    nutrition_data = get_nutrition_analysis(user_id)

    workouts = get_recent_workouts(user_id)

    if not user_profile:
        return "No user profile found."

    if not recovery_data:
        return "No recovery data found."

    if not nutrition_data:
        return "No nutrition data found."

    if not workouts:
        return "No workout data found."

    # -----------------------------
    # Nutrition Summary
    # -----------------------------

    nutrition_summary = ""

    for nutrient_name, nutrient_data in nutrition_data.items():
        nutrition_summary += (
            f"{nutrient_name}: {nutrient_data['amount']} {nutrient_data['unit']}\n"
        )

    # -----------------------------
    # Workout Summary
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
                f"- {set_data['name']} | "
                f"{set_data['reps']} reps x "
                f"{set_data['weight']} lbs"
            )

            if set_data["rir"] is not None:
                workout_summary += f" | RIR {set_data['rir']}"

            workout_summary += "\n"

    # -----------------------------
    # Local LLM
    # -----------------------------

    fast_llm = LLM(model="ollama/qwen3:8b", base_url="http://localhost:11434")
    smart_llm = LLM(model="ollama/qwen3:8b", base_url="http://localhost:11434")

    # -----------------------------
    # Recovery Agent
    # -----------------------------

    recovery_agent = Agent(
        role="Recovery Coach",
        goal="""
        Analyze recovery trends and training readiness.
        """,
        backstory="""
        You specialize in recovery management,
        fatigue analysis,
        and training readiness.
        """,
        llm=fast_llm,
        verbose=True,
    )

    recovery_task = Task(
        description=f"""
        Analyze the following user profile and recovery data.

        User Profile:
        Name: {user_profile["name"]}
        Goal: {user_profile["primary_goal"]}

        Recovery Metrics:
        Average sleep: {recovery_data["avg_sleep"]}
        Average energy: {recovery_data["avg_energy"]}
        Average soreness: {recovery_data["avg_soreness"]}
        Weight change: {recovery_data["weight_change"]}

        Provide:
        1. Recovery assessment
        2. Training readiness
        3. Recovery recommendations
        """,
        expected_output="""
        Concise recovery analysis.
        """,
        agent=recovery_agent,
    )

    # -----------------------------
    # Nutrition Agent
    # -----------------------------

    nutrition_agent = Agent(
        role="Nutrition Coach",
        goal="""
        Analyze nutrition intake and recovery support.
        """,
        backstory="""
        You specialize in performance nutrition,
        body composition,
        and recovery nutrition.
        """,
        llm=fast_llm,
        verbose=True,
    )

    nutrition_task = Task(
        description=f"""
        Analyze macro and micronutrient intake,
        recovery support,
        overall nutrition quality,
        and performance implications.

        Nutrition Data:
        {nutrition_summary}

        Provide:
        1. Nutrition assessment
        2. Recovery implications
        3. Nutrition recommendations
        """,
        expected_output="""
        Concise nutrition analysis.
        """,
        agent=nutrition_agent,
    )

    # -----------------------------
    # Workout Agent
    # -----------------------------

    workout_agent = Agent(
        role="Strength Coach",
        goal="""
        Analyze workout quality and training balance.
        """,
        backstory="""
        You specialize in resistance training,
        recovery management,
        and performance progression.
        """,
        llm=fast_llm,
        verbose=True,
    )

    workout_task = Task(
        description=f"""
        Analyze the following workout history.

        Workout Data:
        {workout_summary}

        Provide:
        1. Workout quality assessment
        2. Recovery implications
        3. Training recommendations
        """,
        expected_output="""
        Concise workout analysis.
        """,
        agent=workout_agent,
    )

    # -----------------------------
    # Coordinator Agent
    # -----------------------------

    coordinator_agent = Agent(
        role="Health Performance Coordinator",
        goal="""
        Combine recovery,
        nutrition,
        and workout insights
        into unified coaching recommendations.
        """,
        backstory="""
        You synthesize recovery,
        nutrition,
        and workout analyses
        into practical,
        actionable health guidance.
        """,
        llm=smart_llm,
        verbose=True,
    )

    coordinator_task = Task(
        description="""
        Combine the recovery,
        nutrition,
        and workout analyses
        into a unified health recommendation.

        Identify:
        1. Biggest issue
        2. Likely cause
        3. Highest priority action
        4. Best recommendation

        Keep response concise and actionable.
        """,
        expected_output="""
        Unified health report.
        """,
        agent=coordinator_agent,
        context=[recovery_task, nutrition_task, workout_task],
    )

    # -----------------------------
    # Build Crew
    # -----------------------------

    crew = Crew(
        agents=[recovery_agent, nutrition_agent, workout_agent, coordinator_agent],
        tasks=[recovery_task, nutrition_task, workout_task, coordinator_task],
        verbose=True,
    )

    # -----------------------------
    # Execute Crew
    # -----------------------------

    print("Recovery agent ready.")
    print("Nutrition agent ready.")
    print("Workout agent ready.")
    print("Coordinator agent ready.")

    print("Starting coordinator crew...")

    try:
        result = crew.kickoff()

        report_text = result.raw

        save_health_report(
            user_id=user_id,
            report_text=report_text,
            model_summary="8B specialists + 8B coordinator",
        )

        return report_text

    except Exception as e:
        print(e)

        return str(e)

from datetime import datetime

from dotenv import load_dotenv

from services.report_service import save_health_report
from services.user_state_service import (
    build_user_health_state,
)

load_dotenv()


def generate_health_report(user_id):
    from crewai import LLM, Agent, Crew, Task

    health_state = build_user_health_state(user_id)

    # -----------------------------
    # Nutrition Summary
    # -----------------------------

    nutrition_summary = health_state.nutrition_state.nutrition_summary

    # -----------------------------
    # Workout Summary
    # -----------------------------

    workout_summary = health_state.training_state.workout_summary

    # -----------------------------
    # Local LLMs
    # -----------------------------

    fast_llm = LLM(
        model="ollama/qwen3:8b",
        base_url="http://localhost:11434",
    )

    smart_llm = LLM(
        model="ollama/qwen3:8b",
        base_url="http://localhost:11434",
    )

    # -----------------------------
    # Recovery Agent
    # -----------------------------

    recovery_agent = Agent(
        role="Recovery Coach",
        goal="Analyze recovery trends and training readiness.",
        backstory="""
        You specialize in recovery management,
        fatigue analysis,
        and training readiness.
        """,
        llm=fast_llm,
        verbose=False,
    )

    recovery_task = Task(
        description=f"""
        Analyze the following user profile and recovery data.

        User Profile:
        Name: {health_state.user_name}
        Goal: {health_state.primary_goal}

        Recovery Metrics:
        Average sleep hours/night: {health_state.recovery_state.avg_sleep}
        Average energy: {health_state.recovery_state.avg_energy}
        Average soreness: {health_state.recovery_state.avg_soreness}
        Weight change: {health_state.recovery_state.weight_change}

        Recovery Interpretation:
        Recovery score: {health_state.recovery_state.recovery_score}
        Fatigue risk: {health_state.recovery_state.fatigue_risk}
        Readiness level: {health_state.recovery_state.readiness_level}
        Sleep trend: {health_state.recovery_state.sleep_trend}
        Weight trend: {health_state.recovery_state.weight_trend}

        Provide:
        1. Recovery assessment
        2. Training readiness
        3. Recovery recommendations
        """,
        expected_output="Concise recovery analysis.",
        agent=recovery_agent,
    )

    # -----------------------------
    # Nutrition Agent
    # -----------------------------

    nutrition_agent = Agent(
        role="Nutrition Coach",
        goal="Analyze nutrition intake and recovery support.",
        backstory="""
        You specialize in performance nutrition,
        body composition,
        and recovery nutrition.
        """,
        llm=fast_llm,
        verbose=False,
    )

    nutrition_task = Task(
        description=f"""
        Analyze macro and micronutrient intake,
        recovery support,
        overall nutrition quality,
        and performance implications.

        Nutrition Data:
        {nutrition_summary}

        Nutrition Interpretation:
        Calories: {health_state.nutrition_state.calories}
        Protein: {health_state.nutrition_state.protein_grams} g
        Carbohydrates: {health_state.nutrition_state.carbohydrate_grams} g
        Fat: {health_state.nutrition_state.fat_grams} g
        Protein status: {health_state.nutrition_state.protein_status}
        Calorie status: {health_state.nutrition_state.calorie_status}
        Recovery nutrition status: {health_state.nutrition_state.recovery_nutrition_status}

        Guardrails:
        - Treat missing nutrition fields as unknown, not zero intake.
        - Do not say the user consumed 0 kcal unless Calories is explicitly logged as 0.
        - If Calories is Unknown, say calorie intake is unavailable or incomplete.
        - Do not infer supplementation, over-supplementation, or true excess micronutrient intake from suspicious values without confirmation.
        - Avoid absolute protein gram targets unless current body weight is available. Use qualitative protein guidance instead.

        Provide:
        1. Nutrition assessment
        2. Recovery implications
        3. Nutrition recommendations
        """,
        expected_output="Concise nutrition analysis.",
        agent=nutrition_agent,
    )

    # -----------------------------
    # Workout Agent
    # -----------------------------

    workout_agent = Agent(
        role="Strength Coach",
        goal="Analyze workout quality and training balance.",
        backstory="""
        You specialize in resistance training,
        recovery management,
        and performance progression.
        """,
        llm=fast_llm,
        verbose=False,
    )

    workout_task = Task(
        description=f"""
        Analyze the following workout history.

        Training Adherence:
        Workout count: {health_state.training_state.workout_count}

        Adherence level: {health_state.training_state.adherence_level}

        Training trend: {health_state.training_state.training_trend}
        Estimated volume load: {health_state.training_state.total_volume_load}
        Average RIR: {health_state.training_state.avg_rir}
        Training load: {health_state.training_state.training_load}
        Recovery demand: {health_state.training_state.recovery_demand}

        RIR guardrail:
        - RIR means reps in reserve.
        - RIR 0-1 means low RIR, high effort, close to failure.
        - RIR 2-3 means moderate effort with more reps left in reserve than RIR 0-1.
        - RIR 4+ means high RIR, lower effort, farther from failure.
        - Never describe RIR 0-1 as high RIR.
        - Never say "lower RIR to 2-3" when current RIR is 0-1.
        - Moving from RIR 0-1 to RIR 2-3 means raising RIR, reducing effort, and leaving more reps in reserve.

        Workout Data:
        {workout_summary}

        Provide:
        1. Workout quality assessment
        2. Recovery implications
        3. Training recommendations
        """,
        expected_output="Concise workout analysis.",
        agent=workout_agent,
    )

    # -----------------------------
    # Coordinator Agent
    # -----------------------------

    coordinator_agent = Agent(
        role="Health Performance Coordinator",
        goal="""
        Combine recovery, nutrition, and workout insights
        into unified coaching recommendations.
        """,
        backstory="""
        You synthesize recovery, nutrition, and workout analyses
        into practical, actionable health guidance.
        """,
        llm=smart_llm,
        verbose=False,
    )

    coordinator_task = Task(
        description=f"""
        Combine the recovery, nutrition, and workout analyses
        into a unified health recommendation.

        System Stress Interpretation:
        System stress level: {health_state.system_stress_level}
        Nutrition/training alignment: {health_state.nutrition_training_alignment}
        Coordinator focus: {health_state.coordinator_focus}

        Critical final report guardrails:
        - Missing nutrition fields are unknown, not zero intake.
        - Do not say 0 kcal, 0 g protein, 0 g carbs, or 0 g fat unless those values were explicitly logged as 0.
        - If nutrition data is incomplete, describe it as incomplete rather than as severe restriction.
        - Average sleep is measured in hours/night, not on a 10-point scale.
        - If average sleep is 5.3, say approximately 5.3 hours/night. Do not say 5.3/10.
        - RIR means reps in reserve.
        - RIR 0-1 means low RIR / high effort / close to failure.
        - RIR 2-3 means more reps left in reserve than RIR 0-1.
        - Moving from RIR 0-1 to RIR 2-3 means raising RIR, reducing effort, and leaving more reps in reserve.
        - Never describe RIR 0-1 as high RIR.
        - Never say "lower RIR to 2-3" when current RIR is 0-1.
        - Treat suspicious micronutrient values cautiously.
        - Do not assume supplementation, over-supplementation, or true intake without confirmation.
        - Do not recommend reducing supplements or fortified foods unless supplementation or fortified-food intake is confirmed.
        - Avoid fixed carbohydrate targets such as 20-40g or 40-60g unless supported by body weight, training volume, and user goal context.
        - For carbohydrate guidance, use contextual wording based on training load, recovery status, body weight, and goals.
        - Avoid absolute protein targets unless current body weight is available.

        Forbidden final report wording:
        - Any phrase that combines "high RIR" or "high-RIR" with "0", "1", or "0-1"
        - "high-RIR lifts (0-1)"
        - "high-RIR session" when referring to RIR 0-1
        - "high RIR (near-failure efforts)"
        - "high RIR risks overtraining"
        - "Replace high-RIR (0-1)"
        - "sleep deprivation (5.3/10)"
        - "likely from supplements"
        - "reduce supplements" unless supplement use is confirmed
        - "20-40g carbs" or "40-60g carbs" as a fixed recommendation without context

        RIR wording requirements:
        - For RIR 0-1, the ONLY acceptable labels are:
          "low RIR", "high effort", "near failure", "close to failure", or "low-RIR/high-effort work".
        - Never pair the phrase "high RIR" with values 0, 1, or 0-1.
        - The phrase "high RIR" may only be used for RIR 4+.
        - If discussing RIR 0-1, always say "low RIR" instead of "high RIR".
        - If recommending RIR 2-3 from current RIR 0-1, say "raise RIR to 2-3" or "move toward RIR 2-3", never "lower RIR."

        Micronutrient wording requirements:
        - Do not use "likely" when explaining suspicious micronutrient values.
        - Use "may reflect" instead.
        - Do not recommend reducing supplements, fortified foods, sodium, calcium, potassium, magnesium, or zinc unless the source is confirmed.
        - Recommend verification first.

        Macro recommendation requirements:
        - Do not give fixed calorie, protein, carbohydrate, sodium, calcium, potassium, magnesium, or zinc targets unless required context is available.
        - Prefer qualitative guidance: "evaluate relative to body weight, training load, recovery status, goals, and logged intake completeness."

        Required replacement language:
        - Say "low-RIR/high-effort work at RIR 0-1."
        - Say "move from RIR 0-1 toward RIR 2-3 temporarily to reduce effort and leave more reps in reserve."
        - Say "approximately 5.3 hours/night," not "5.3/10."
        - Say "some micronutrient values appear unusually high and may reflect logging, database, unit, or supplementation artifacts; verify before acting."
        - For carbohydrates, say "carbohydrate intake should be evaluated relative to training load, recovery, body weight, and goals" instead of giving fixed low gram targets.

        Identify:
        1. Biggest issue
        2. Likely cause
        3. Highest priority action
        4. Best recommendation

        Keep response concise and actionable.
        """,
        expected_output="Unified health report.",
        agent=coordinator_agent,
        context=[
            recovery_task,
            nutrition_task,
            workout_task,
        ],
    )

    # -----------------------------
    # Build Crew
    # -----------------------------

    crew = Crew(
        agents=[
            recovery_agent,
            nutrition_agent,
            workout_agent,
            coordinator_agent,
        ],
        tasks=[
            recovery_task,
            nutrition_task,
            workout_task,
            coordinator_task,
        ],
        verbose=False,
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
        print("\nCalling crew.kickoff()...\n")
        print("DEBUG MARKER")

        result = crew.kickoff()

        print("\ncrew.kickoff() completed.\n")

        timestamp = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

        final_report = f"Generated: {timestamp}\n\n{result.raw}"

        save_health_report(
            user_id=user_id,
            report_text=final_report,
            model_summary="ollama/qwen3:8b",
        )

        return final_report

    except Exception as e:
        print("\n=== CREWAI ERROR ===\n")
        print(type(e))
        print(e)

        import traceback

        traceback.print_exc()

        return str(e)


if __name__ == "__main__":
    report = generate_health_report(1)

    print("\n=== FINAL REPORT ===\n")
    print(report)

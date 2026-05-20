from dotenv import load_dotenv

load_dotenv()

from crewai import Agent, Task, Crew, LLM

from services.nutrition_service import get_nutrition_analysis
from services.user_service import get_user_profile

from models.nutrition_models import NutritionAssessment

# -----------------------------
# Select User
# -----------------------------

user_id = int(input("User ID: "))

user_profile = get_user_profile(user_id)

nutrition_data = get_nutrition_analysis(user_id)


# -----------------------------
# Validate Data
# -----------------------------

nutrition_summary = ""

if not nutrition_data:

    nutrition_summary = "No nutrition data logged today."

else:

    # -----------------------------
    # Build Dynamic Nutrition Summary
    # -----------------------------

    for nutrient_name, nutrient_data in nutrition_data.items():

        nutrition_summary += (
            f"{nutrient_name}: "
            f"{nutrient_data['amount']} "
            f"{nutrient_data['unit']}\n"
        )


# -----------------------------
# Local LLM
# -----------------------------

fast_llm = LLM(model="ollama/qwen2.5:3b", base_url="http://localhost:11434")

smart_llm = LLM(model="ollama/qwen3:8b", base_url="http://localhost:11434")

llm = fast_llm

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
    micronutrients,
    recovery nutrition,
    and performance optimization.
    """,
    llm=llm,
    verbose=True,
    response_format=NutritionAssessment,
)


# -----------------------------
# Nutrition Task
# -----------------------------

nutrition_task = Task(
    description=f"""
    Analyze the following user profile and nutrition data,
    including macro and micronutrient intake,
    recovery support,
    overall nutrition quality,
    and potential deficiencies.

    User Profile:
    Name: {user_profile['name']}
    Gender: {user_profile['gender']}
    Age: {user_profile['age']}
    Height: {user_profile['height_cm']} cm
    Starting Weight: {user_profile['starting_weight']}
    Goal Weight: {user_profile['goal_weight']}
    Primary Goal: {user_profile['primary_goal']}
    Activity Level: {user_profile['activity_level']}

    Nutrition Data:
    {nutrition_summary}

    Analyze:
    1. Macronutrient quality
    2. Micronutrient quality
    3. Recovery support
    4. Potential deficiencies
    5. Overall nutrition quality

    Return your response in this exact structure:

    {{
        "nutrition_score": integer from 1-10,
        "protein_status": "low/moderate/high",
        "calorie_status": "low/moderate/high",
        "recovery_impact": "low/moderate/high",
        "recommendation": "concise recommendation"
    }}
    """,
    expected_output="""
    Structured nutrition assessment.
    """,
    agent=nutrition_agent,
)


# -----------------------------
# Build Crew
# -----------------------------

crew = Crew(agents=[nutrition_agent], tasks=[nutrition_task], verbose=True)


# -----------------------------
# Run Workflow
# -----------------------------

result = crew.kickoff()

print("\n=== NUTRITION REPORT ===\n")
print(result)

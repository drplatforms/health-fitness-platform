from crewai import LLM, Agent, Crew, Task
from dotenv import load_dotenv

from models.recovery_models import RecoveryAssessment
from services.recovery_service import get_recent_recovery_metrics, save_recovery_report

load_dotenv()

# -----------------------------
# Load Recovery Metrics
# -----------------------------

metrics = get_recent_recovery_metrics()

if not metrics:
    print("No recovery data found.")
    exit()


# -----------------------------
# LLM Configuration
# -----------------------------

fast_llm = LLM(model="ollama/qwen2.5:3b", base_url="http://localhost:11434")

smart_llm = LLM(model="ollama/qwen3:8b", base_url="http://localhost:11434")

# Choose model for this agent
llm = fast_llm


# -----------------------------
# Recovery Agent
# -----------------------------

recovery_agent = Agent(
    role="Fitness Recovery Coach",
    goal="""
    Help users optimize recovery
    and training readiness.
    """,
    backstory="""
    You are an experienced recovery
    and performance coach.

    You analyze:
    - sleep quality
    - soreness
    - fatigue
    - recovery readiness

    You provide concise,
    practical recommendations.
    """,
    llm=llm,
    verbose=True,
    response_format=RecoveryAssessment,
)


# -----------------------------
# Recovery Task
# -----------------------------

task = Task(
    description=f"""
    Analyze the following recovery metrics:

    Entries analyzed:
    {metrics["entries_analyzed"]}

    Average sleep:
    {metrics["avg_sleep"]} hours

    Average energy:
    {metrics["avg_energy"]}/10

    Average soreness:
    {metrics["avg_soreness"]}/10

    Weight change:
    {metrics["weight_change"]} lbs

    Recent notes:
    {metrics["recent_notes"]}

    Provide:

    1. Recovery assessment
    2. Training recommendation
    3. Nutrition/recovery suggestion

    Keep the response concise
    and practical.
    """,
    expected_output="""
    A concise recovery and
    training recommendation.
    """,
    agent=recovery_agent,
)


# -----------------------------
# Build Crew
# -----------------------------

crew = Crew(agents=[recovery_agent], tasks=[task], verbose=True)


# -----------------------------
# Run Workflow
# -----------------------------

print("\nStarting recovery agent...\n")

result = crew.kickoff()


# -----------------------------
# Save Recovery Report
# -----------------------------

save_recovery_report(metrics, str(result))


# -----------------------------
# Output
# -----------------------------

print("\n=== RECOVERY REPORT ===\n")

print(result)

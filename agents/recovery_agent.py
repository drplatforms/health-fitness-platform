from dotenv import load_dotenv
load_dotenv()

from crewai import Agent, Task, Crew, LLM

from models.recovery_models import RecoveryAssessment

from services.recovery_service import (
    get_recent_recovery_metrics,
    save_recovery_report
)


# Get recovery metrics from SQLite
metrics = get_recent_recovery_metrics()

if not metrics:
    print("No recovery data found.")
    exit()


# Connect to local Ollama model
llm=fast_llm


# Create recovery coach agent
recovery_agent = Agent(
    role="Fitness Recovery Coach",
    goal="Help users optimize recovery and training readiness",
    backstory="""
    You are an experienced recovery and performance coach.
    You analyze training recovery metrics and provide concise,
    practical recommendations.
    """,
    llm=llm,
    verbose=True,
    
    response_format=RecoveryAssessment
)


# Create task dynamically using REAL database data
task = Task(
    description=f"""
    Analyze the following recovery metrics:

    Entries analyzed: {metrics['entries_analyzed']}
    Average sleep: {metrics['avg_sleep']} hours
    Average energy: {metrics['avg_energy']}/10
    Average soreness: {metrics['avg_soreness']}/10
    Weight change: {metrics['weight_change']} lbs

    Recent notes:
    {metrics['recent_notes']}

    Provide:
    1. Recovery assessment
    2. Training recommendation
    3. Nutrition/recovery suggestion

    Keep the response concise and practical.
    """,

    expected_output="""
    A concise recovery and training recommendation.
    """,

    agent=recovery_agent
)


# Build crew
crew = Crew(
    agents=[recovery_agent],
    tasks=[task],
    verbose=True
)


# Run workflow
result = crew.kickoff()

#Save AI Recommenation
save_recovery_report(metrics, str(result))

print("\n=== RECOVERY REPORT ===\n")
print(result)
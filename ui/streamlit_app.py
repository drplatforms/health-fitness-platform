import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import plotly.express as px

sys.path.append(
    str(Path(__file__).resolve().parent.parent)
)

import streamlit as st

from services.user_service import get_all_users

from services.recovery_service import (
    get_recent_recovery_reports
)

from services.nutrition_service import (
    get_daily_nutrition
)

from services.coordinator_service import (
    generate_health_report
)

from services.report_service import (
    get_latest_health_report,
    get_health_report_history
)

from services.workout_service import (
    get_recent_workouts,
    get_exercises,
    create_workout_session,
    add_workout_set
)


# -----------------------------
# Page Config
# -----------------------------

st.set_page_config(
    page_title="Fitness AI Dashboard",
    layout="wide"
)


# -----------------------------
# Title
# -----------------------------

st.title("🏋️ Fitness AI Dashboard")


# -----------------------------
# Session State
# -----------------------------

if "current_sets" not in st.session_state:
    st.session_state.current_sets = []

if "health_report" not in st.session_state:
    st.session_state.health_report = None

if "health_report_timestamp" not in st.session_state:
    st.session_state.health_report_timestamp = None


# -----------------------------
# User Selection
# -----------------------------

users = get_all_users()

user_map = {
    f"{user['id']} - {user['name']}": user["id"]
    for user in users
}

selected_user = st.sidebar.selectbox(
    "Select User",
    list(user_map.keys())
)

user_id = user_map[selected_user]


# -----------------------------
# Load Cached Report
# -----------------------------

if st.session_state.health_report is None:

    latest_report = get_latest_health_report(user_id)

    if latest_report:

        st.session_state.health_report = (
            latest_report["report_text"]
        )

        st.session_state.health_report_timestamp = (
            latest_report["created_at"]
        )


# -----------------------------
# Sidebar Actions
# -----------------------------

if st.sidebar.button(
    "Refresh AI Report",
    key="refresh_ai_report"
):
    st.session_state.health_report = None


if st.sidebar.button(
    "Load Latest Saved Report",
    key="load_latest_report"
):

    latest_report = get_latest_health_report(user_id)

    if latest_report:

        st.session_state.health_report = (
            latest_report["report_text"]
        )

        st.session_state.health_report_timestamp = (
            latest_report["created_at"]
        )

        st.success("Latest saved report loaded.")

    else:

        st.warning("No saved reports found.")


# -----------------------------
# Recovery Section
# -----------------------------

st.header("🛌 Recovery")

recovery_reports = get_recent_recovery_reports()

if recovery_reports:

    latest = recovery_reports[0]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Avg Sleep",
        round(latest["avg_sleep"], 1)
    )

    col2.metric(
        "Avg Energy",
        round(latest["avg_energy"], 1)
    )

    col3.metric(
        "Avg Soreness",
        round(latest["avg_soreness"], 1)
    )

    col4.metric(
        "Weight Change",
        round(latest["weight_change"], 1)
    )

    st.write("### Recommendation")
    st.info(latest["recommendation"])

else:

    st.warning("No recovery reports found.")


# -----------------------------
# Recovery Trends
# -----------------------------

recovery_df = pd.DataFrame(
    recovery_reports
)

if not recovery_df.empty:

    recovery_df = recovery_df.copy()

    recovery_df["report_number"] = range(
        1,
        len(recovery_df) + 1
    )

    fig = px.line(
        recovery_df,
        x="report_number",
        y=[
            "avg_sleep",
            "avg_energy",
            "avg_soreness"
        ],
        markers=True,
        title="Recovery Trends"
    )

    st.plotly_chart(
        fig,
        width="stretch"
    )

else:

    st.warning(
        "No recovery report data available."
    )


# -----------------------------
# Nutrition Section
# -----------------------------

st.header("🍎 Nutrition")

today = datetime.now().strftime("%Y-%m-%d")

nutrition = get_daily_nutrition(
    user_id,
    today
)

if nutrition:

    nutrition_rows = []

    for nutrient_name, nutrient_data in nutrition.items():

        nutrition_rows.append({
            "Nutrient": nutrient_name,
            "Amount": nutrient_data["amount"],
            "Unit": nutrient_data["unit"]
        })

    st.dataframe(
        nutrition_rows,
        width="stretch"
    )

else:
    st.warning("No nutrition data found.")


# -----------------------------
# Workout Logger
# -----------------------------

st.header("📝 Log Workout")

workout_name = st.text_input(
    "Workout Name"
)

duration_minutes = st.number_input(
    "Duration (minutes)",
    min_value=0,
    value=60
)

notes = st.text_area(
    "Workout Notes"
)

exercises = get_exercises()

exercise_map = {
    exercise["name"]: exercise["id"]
    for exercise in exercises
}

selected_exercise = st.selectbox(
    "Exercise",
    list(exercise_map.keys())
)

set_number = st.number_input(
    "Set Number",
    min_value=1,
    value=1
)

reps = st.number_input(
    "Reps",
    min_value=1,
    value=10
)

weight = st.number_input(
    "Weight",
    min_value=0.0,
    value=0.0,
    step=5.0
)

rir = st.number_input(
    "RIR",
    min_value=0,
    max_value=5,
    value=2
)


# -----------------------------
# Add Set
# -----------------------------

if st.button(
    "Add Set",
    key="add_set_button"
):

    st.session_state.current_sets.append({
        "exercise_id": exercise_map[selected_exercise],
        "exercise_name": selected_exercise,
        "set_number": set_number,
        "reps": reps,
        "weight": weight,
        "rir": rir
    })

    st.success("Set added.")


# -----------------------------
# Current Workout Preview
# -----------------------------

if st.session_state.current_sets:

    st.write("### Current Workout")

    for set_data in st.session_state.current_sets:

        st.write(
            f"{set_data['exercise_name']} | "
            f"Set {set_data['set_number']} | "
            f"{set_data['reps']} reps x "
            f"{set_data['weight']} lbs | "
            f"RIR {set_data['rir']}"
        )


# -----------------------------
# Save Workout
# -----------------------------

if st.button(
    "Save Workout",
    key="save_workout_button"
):

    session_id = create_workout_session(
        user_id=user_id,
        workout_name=workout_name,
        duration_minutes=duration_minutes,
        notes=notes
    )

    for set_data in st.session_state.current_sets:

        add_workout_set(
            workout_session_id=session_id,
            exercise_id=set_data["exercise_id"],
            set_number=set_data["set_number"],
            reps=set_data["reps"],
            weight=set_data["weight"],
            rir=set_data["rir"]
        )

    st.success("Workout saved.")

    st.session_state.current_sets = []


# -----------------------------
# Recent Workouts
# -----------------------------

st.header("🏋️ Recent Workouts")

workouts = get_recent_workouts(user_id)

if workouts:

    for workout in workouts:

        session = workout["session"]

        with st.expander(
            f"{session['workout_name']} - "
            f"{session['workout_date']}"
        ):

            st.write(
                f"Duration: "
                f"{session['duration_minutes']}"
            )

            st.write(
                f"Notes: "
                f"{session['notes']}"
            )

            for set_data in workout["sets"]:

                text = (
                    f"{set_data['name']} | "
                    f"{set_data['reps']} reps x "
                    f"{set_data['weight']} lbs"
                )

                if set_data["rir"] is not None:
                    text += f" | RIR {set_data['rir']}"

                st.write(text)

else:
    st.warning("No workouts found.")


# -----------------------------
# AI Health Coordinator
# -----------------------------

st.header("🧠 AI Health Insights")

if st.session_state.health_report_timestamp:

    st.caption(
        f"Last Generated: "
        f"{st.session_state.health_report_timestamp}"
    )

if st.button(
    "Generate AI Health Report",
    key="generate_ai_report_button"
):

    with st.spinner("Running multi-agent health coordinator..."):

        new_report = generate_health_report(user_id)

        st.session_state.health_report = new_report

        st.session_state.health_report_timestamp = (
            datetime.now().strftime("%Y-%m-%d %I:%M %p")
        )

if st.session_state.health_report:
    st.write(st.session_state.health_report)

else:
    st.info(
        "Click the button to generate a new AI health report."
    )


# -----------------------------
# AI Report History
# -----------------------------

st.header("🧠 Report History")

report_history = get_health_report_history(
    user_id,
    limit=5
)

if report_history:

    for report in report_history:

        with st.expander(
            f"Report - {report['created_at']}"
        ):

            st.write(report["report_text"])

else:

    st.info("No report history found.")

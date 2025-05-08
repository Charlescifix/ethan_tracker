# ===========================
# Streamlit Form Builder
# ===========================

import streamlit as st
from datetime import datetime


def training_form(default_date=None):
    """
    Builds a fancy interactive form for data input.

    Args:
        default_date (date, optional): Default date to use in the form
    """
    # Use the default date if provided, otherwise use current date
    date_value = default_date if default_date is not None else datetime.now()

    # 📅 Date Picker - using your preferred style
    date = st.date_input("Select Training Date", date_value)

    # 🔄 Session Type
    session_type = st.selectbox(
        "Select Training Type",
        ["Physical Training", "Match", "Club Training", "Home Training"]
    )

    # ⏳ Duration
    duration_mins = st.slider("Duration (minutes)", 15, 120, 60)

    # 🏅 Position Played
    position = st.radio(
        "Position Played",
        ["Right Wing (RW)", "Striker (ST)", "None (Bench/Fitness Only)"],
        horizontal=True
    )

    # ===========================
    # Conditional Inputs
    # ===========================
    if session_type != "Physical Training":
        # ⚽ Goals & Assists
        goals = st.number_input("Goals Scored", 0, 10, step=1)
        assists = st.number_input("Assists", 0, 10, step=1)

        # 🛡️ Tackles, Passes, Crosses, and Shots
        tackles = st.slider("Tackles Made", 0, 20, 5)
        passes_completed = st.slider("Passes Completed", 0, 50, 20)
        crosses = st.slider("Crosses Delivered", 0, 20, 5)
        shots_on_target = st.slider("Shots on Target", 0, 10, 3)
    else:
        # If it's Physical Training, these are irrelevant
        goals = assists = tackles = passes_completed = crosses = shots_on_target = 0

    # 🌟 Player Rating (Emoji-based)
    rating = st.select_slider(
        "Player Rating",
        options=[1, 2, 3, 4, 5],
        format_func=lambda x: "⭐" * x
    )

    # 💬 Comments
    comments = st.text_area("Comments (Optional)")

    # ✅ Submit Button
    if st.button("Save Training Session"):
        st.success("Training Session Saved Successfully! ✅")

        # Collect the data into a dictionary
        form_data = {
            "date": date,
            "session_type": session_type,
            "duration_mins": duration_mins,
            "position": position,
            "goals": goals,
            "assists": assists,
            "tackles": tackles,
            "passes_completed": passes_completed,
            "crosses": crosses,
            "shots_on_target": shots_on_target,
            "rating": rating,
            "comments": comments
        }
        return form_data

# ===========================
# Ethan's Football Growth & Performance Tracker - Enhanced Main App
# ===========================

import streamlit as st
import pandas as pd
from utils.form_builder import training_form
from utils.data_handler import save_training_session, fetch_all_sessions, create_table, delete_session
from models.training_session import TrainingSession
from datetime import datetime, timedelta
import plotly.express as px

# Create the table if not exists
create_table()

# Page Configuration
st.set_page_config(
    page_title="Ethan's Football Growth & Performance Tracker",
    page_icon="⚽",
    layout="wide"
)

# App Title and Description
st.title("⚽ Ethan's Football Growth & Performance Tracker")
st.write("Track Ethan's football growth, performance metrics, and progress over time. 🏅")

# Create tabs
tab1, tab2, tab3 = st.tabs(["📝 Add New Session", "📊 Quick Stats", "⚙️ Manage Data"])

# ===========================
# Tab 1: Add New Session Form
# ===========================
with tab1:
    st.header("📝 Record New Training Session")

    # Quick selector for today or yesterday
    quick_date = st.radio(
        "Quick Date Select:",
        ["Custom Date", "Today", "Yesterday"],
        horizontal=True
    )

    today = datetime.today().date()

    if quick_date == "Today":
        default_date = today
    elif quick_date == "Yesterday":
        default_date = today - timedelta(days=1)
    else:
        default_date = None

    # Display the Form with optional default date
    form_data = training_form(default_date=default_date)

    # If form submission is successful, create a TrainingSession object and save it
    if form_data:
        # Handle "None (Bench/Fitness Only)" as a valid position
        position_value = form_data['position'] if form_data['position'] != "None (Bench/Fitness Only)" else None

        training_session = TrainingSession(
            date=form_data['date'],
            session_type=form_data['session_type'],
            duration_mins=form_data['duration_mins'],
            position=position_value,
            goals=form_data['goals'],
            assists=form_data['assists'],
            tackles=form_data['tackles'],
            passes_completed=form_data['passes_completed'],
            crosses=form_data['crosses'],
            shots_on_target=form_data['shots_on_target'],
            rating=form_data['rating'],
            comments=form_data['comments']
        )

        # Save to PostgreSQL database
        save_training_session(training_session)

        # Display Success Message
        st.success("✅ Training Session Saved Successfully!")

        # Add option to add another session
        st.button("Add Another Session", type="primary", use_container_width=True)

# ===========================
# Tab 2: Quick Stats
# ===========================
with tab2:
    st.header("📊 Quick Stats Overview")

    # Fetch data
    data = fetch_all_sessions()

    if not data:
        st.warning("No data found. Please add some training sessions first in the 'Add New Session' tab.")
    else:
        # Convert to DataFrame
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by='date', ascending=False)

        # Fill missing values
        numeric_cols = ['goals', 'assists', 'tackles', 'passes_completed',
                        'crosses', 'shots_on_target', 'rating', 'duration_mins']
        df[numeric_cols] = df[numeric_cols].fillna(0)

        # Calculate derived metrics
        df['goal_contributions'] = df['goals'] + df['assists']

        # Show recent performance
        st.subheader("Recent Performance")

        # Create metrics
        col1, col2, col3, col4 = st.columns(4)

        # Latest session
        latest = df.iloc[0]
        previous = df.iloc[1] if len(df) > 1 else None

        col1.metric(
            "Last Session Rating ⭐",
            f"{latest['rating']:.1f}",
            f"{latest['rating'] - previous['rating']:.1f}" if previous is not None else None
        )

        # Last 5 sessions average
        last_5_avg = df.head(5)['rating'].mean()
        all_time_avg = df['rating'].mean()

        col2.metric(
            "5-Session Avg ⭐",
            f"{last_5_avg:.1f}",
            f"{last_5_avg - all_time_avg:.1f}"
        )

        # Recent goals
        recent_goals = df.head(5)['goals'].sum()
        col3.metric("Recent Goals (5) ⚽", recent_goals)

        # Recent assists
        recent_assists = df.head(5)['assists'].sum()
        col4.metric("Recent Assists (5) 🎯", recent_assists)

        # Show last 5 sessions
        st.subheader("Last 5 Sessions")
        recent_df = df.head(5)[['date', 'session_type', 'position', 'goals', 'assists', 'rating']]
        recent_df['position'] = recent_df['position'].fillna("🏋️ Physical Only")
        st.dataframe(recent_df, use_container_width=True)

        # Create 2 columns
        col1, col2 = st.columns(2)

        with col1:
            # Show recent ratings
            st.subheader("Recent Ratings")
            recent_ratings = df.head(10).sort_values('date')
            recent_ratings['session_num'] = range(1, len(recent_ratings) + 1)

            fig = px.line(
                recent_ratings,
                x='session_num',
                y='rating',
                markers=True,
                text='rating',
                title="Last 10 Sessions Rating Trend",
                labels={'session_num': 'Session #', 'rating': 'Rating'}
            )

            fig.update_traces(textposition="top center")
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Show goal contribution distribution
            st.subheader("Goal Contributions")

            if df['goals'].sum() > 0 or df['assists'].sum() > 0:
                goal_data = pd.DataFrame({
                    'Type': ['Goals', 'Assists'],
                    'Count': [df['goals'].sum(), df['assists'].sum()]
                })

                fig = px.pie(
                    goal_data,
                    values='Count',
                    names='Type',
                    title='Goals vs Assists Distribution',
                    color_discrete_map={'Goals': 'rgb(39, 128, 227)', 'Assists': 'rgb(39, 227, 128)'},
                    hole=0.4
                )

                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=300, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No goals or assists recorded yet.")

        # Link to full dashboard
        st.info("For more detailed analysis, visit the Dashboard page.")

        # Show calendar heatmap of activity
        st.subheader("Activity Calendar")

        # Prepare calendar data
        cal_df = df.copy()
        cal_df['date_str'] = cal_df['date'].dt.strftime('%Y-%m-%d')
        cal_df = cal_df.groupby('date_str').agg({
            'rating': 'mean',
            'session_type': 'count'
        }).reset_index()
        cal_df.columns = ['date', 'avg_rating', 'sessions']

        fig = px.scatter(
            cal_df,
            x='date',
            y=['avg_rating'],
            size='sessions',
            color='avg_rating',
            color_continuous_scale='YlGnBu',
            title="Training Activity Calendar",
            labels={'date': 'Date', 'avg_rating': 'Avg. Rating', 'sessions': 'Sessions'}
        )

        fig.update_layout(height=300, yaxis_title="Rating")
        st.plotly_chart(fig, use_container_width=True)

# ===========================
# Tab 3: Manage Data
# ===========================
with tab3:
    st.header("⚙️ Manage Training Data")

    # Fetch all sessions for management
    data = fetch_all_sessions()

    if not data:
        st.warning("No data found. Please add some training sessions first.")
    else:
        # Convert to DataFrame
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values(by='date', ascending=False)

        # Fill missing values for display
        df['position'] = df['position'].fillna("🏋️ Physical Only")

        # Show warning
        st.warning("⚠️ Caution: Data management actions cannot be undone.")

        # Create an expander for the delete function to prevent accidental clicks
        with st.expander("Delete Training Session"):
            st.subheader("Select Session to Delete")

            # Create session selection options
            session_options = [f"{row['date'].strftime('%Y-%m-%d')} - {row['session_type']} - Rating: {row['rating']}"
                               for _, row in df.iterrows()]

            selected_session = st.selectbox(
                "Select a session to delete:",
                options=session_options,
                index=None,
                placeholder="Choose a session..."
            )

            if selected_session:
                # Get index of selected session
                selected_idx = session_options.index(selected_session)
                selected_row = df.iloc[selected_idx]

                # Show confirmation
                st.write(f"You selected: **{selected_session}**")

                # Show session details
                st.write("Session details:")
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Date 📅", selected_row['date'].strftime('%Y-%m-%d'))
                col2.metric("Type 🎯", selected_row['session_type'])
                col3.metric("Position 👤", selected_row['position'])
                col4.metric("Rating ⭐", selected_row['rating'])

                # Confirmation checkbox
                confirm = st.checkbox("I confirm I want to delete this session")

                if confirm:
                    if st.button("Delete Session", type="primary"):
                        # Delete session from database
                        delete_session(selected_row['id'])
                        st.success("✅ Session deleted successfully!")
                        st.rerun()  # Refresh the page

        # Display all sessions in a table
        st.subheader("All Training Sessions")
        st.dataframe(
            df[['date', 'session_type', 'position', 'goals', 'assists', 'tackles', 'rating', 'duration_mins']],
            use_container_width=True
        )

        # Data Export Option
        st.subheader("Export Data")

        export_format = st.radio(
            "Export Format:",
            ["CSV", "Excel"],
            horizontal=True
        )

        if st.button("Download Data", type="primary"):
            # Prepare data for download
            export_df = df.copy()
            export_df['date'] = export_df['date'].dt.strftime('%Y-%m-%d')

            if export_format == "CSV":
                csv = export_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"ethan_football_data_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            else:
                # For Excel format, we need to convert to bytes
                # Here, we'd typically use BytesIO and pandas to_excel
                # For Streamlit, a simplified approach:
                st.info("Excel export functionality will be implemented in the next version.")

        # Add backup reminder
        st.info("💡 Tip: Regularly export your data as a backup.")

# Add footer with navigation links
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

with col2:
    st.markdown("Made with ❤️ for Ethan")
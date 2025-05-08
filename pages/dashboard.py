# ===========================
# Ethan's Football Growth & Performance Tracker - Enhanced Dashboard
# ===========================

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from utils.data_handler import fetch_all_sessions
import calendar
from datetime import datetime, timedelta

# ===========================
# Page Configuration
# ===========================
st.set_page_config(page_title="Dashboard - Ethan's Growth Tracker", page_icon="📊", layout="wide")
st.title("📊 Ethan's Performance Dashboard")
st.markdown("Visualize Ethan's growth and match stats over time. 📈")

# ===========================
# Fetch Data from Database
# ===========================
data = fetch_all_sessions()

if not data:
    st.warning("No data found. Please add some training sessions first.")
else:
    try:
        # Convert list of dicts to DataFrame
        df = pd.DataFrame(data)

        # Ensure 'date' is datetime
        df['date'] = pd.to_datetime(df['date'])

        # Add month and week columns for time-based analysis
        df['month'] = df['date'].dt.month_name()
        df['week'] = df['date'].dt.isocalendar().week
        df['month_num'] = df['date'].dt.month

        # Sort by date
        df = df.sort_values(by='date')

        # Calculate derived metrics
        df['goal_contributions'] = df['goals'] + df['assists']
        df['offensive_actions'] = df['shots_on_target'] + df['crosses']
        df['defensive_actions'] = df['tackles']

        # Handle NaN values
        numeric_columns = ['goals', 'assists', 'tackles', 'passes_completed',
                           'crosses', 'shots_on_target', 'rating', 'duration_mins']
        df[numeric_columns] = df[numeric_columns].fillna(0)

        # Handle None gracefully for position
        df['position'] = df['position'].fillna("🏋️ Physical Only")

        # ===========================
        # Top Level KPI Metrics
        # ===========================
        st.subheader("⚽ Performance Summary")

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Goals ⚽", df['goals'].sum())
        col2.metric("Total Assists 🎯", df['assists'].sum())
        col3.metric("Avg. Rating ⭐", f"{df['rating'].mean():.2f}")
        col4.metric("Total Training Hours ⏱️", f"{df['duration_mins'].sum() / 60:.1f}")

        # Calculate form - average rating of last 5 sessions
        last_5_avg = df.tail(5)['rating'].mean()
        all_time_avg = df['rating'].mean()
        rating_diff = last_5_avg - all_time_avg

        col5.metric("Current Form 🔥", f"{last_5_avg:.2f}",
                    f"{rating_diff:+.2f}",
                    delta_color="normal" if rating_diff >= 0 else "inverse")

        # Position summary
        if not df['position'].isnull().all():
            top_position = df['position'].mode()[0]
            if top_position == "🏋️ Physical Only":
                st.info(f"🔝 Most Sessions: **Physical Training** 🏋️")
            else:
                st.info(f"🔝 Most Played Position: **{top_position}**")

        # ===========================
        # Recent Sessions Table
        # ===========================
        with st.expander("📅 Recent Training Sessions", expanded=False):
            display_df = df[['date', 'session_type', 'position', 'goals', 'assists', 'rating']].copy()
            display_df = display_df.sort_values(by='date', ascending=False)
            st.dataframe(display_df, use_container_width=True)

        # ===========================
        # Main Dashboard - Two Column Layout
        # ===========================
        left_col, right_col = st.columns([3, 2])

        with left_col:
            # ===========================
            # Monthly Performance Trends - Area Chart
            # ===========================
            st.subheader("📈 Monthly Performance Trends")

            # Group by month and calculate averages
            monthly_metrics = df.groupby('month_num').agg({
                'goals': 'sum',
                'assists': 'sum',
                'rating': 'mean',
                'passes_completed': 'mean',
                'tackles': 'mean',
                'shots_on_target': 'mean'
            }).reset_index()

            # Add month names for better labeling
            month_names = {i: calendar.month_name[i] for i in range(1, 13)}
            monthly_metrics['month'] = monthly_metrics['month_num'].map(month_names)
            monthly_metrics = monthly_metrics.sort_values('month_num')

            # Create a multi-line chart
            fig = px.line(monthly_metrics, x='month', y=['goals', 'assists', 'rating'],
                          title="Monthly Goal Contributions & Ratings",
                          labels={'value': 'Count/Rating', 'variable': 'Metric'},
                          line_shape='spline', markers=True)

            fig.update_layout(height=400, hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)

            # ===========================
            # Performance by Position - Radar Chart
            # ===========================
            st.subheader("🎯 Performance by Position")

            # Filter out physical training
            match_df = df[df['position'] != "🏋️ Physical Only"]

            if not match_df.empty and len(match_df['position'].unique()) > 1:
                # Group by position and calculate averages
                position_stats = match_df.groupby('position').agg({
                    'goals': 'mean',
                    'assists': 'mean',
                    'tackles': 'mean',
                    'passes_completed': 'mean',
                    'crosses': 'mean',
                    'shots_on_target': 'mean',
                    'rating': 'mean'
                }).reset_index()

                # Create radar chart
                fig = go.Figure()

                # Add traces for each position
                for position in position_stats['position']:
                    position_data = position_stats[position_stats['position'] == position]

                    fig.add_trace(go.Scatterpolar(
                        r=[
                            position_data['goals'].values[0],
                            position_data['assists'].values[0],
                            position_data['tackles'].values[0],
                            position_data['passes_completed'].values[0],
                            position_data['crosses'].values[0],
                            position_data['shots_on_target'].values[0],
                            position_data['rating'].values[0]
                        ],
                        theta=['Goals', 'Assists', 'Tackles', 'Passes', 'Crosses', 'Shots', 'Rating'],
                        fill='toself',
                        name=position
                    ))

                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                        )
                    ),
                    height=500,
                    showlegend=True
                )

                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Not enough position data to create a comparison radar chart")

            # ===========================
            # Goals + Assists Timeline - Combined Area Chart
            # ===========================
            st.subheader("⚽ Goal Contributions Timeline")

            # Prepare data for timeline
            timeline_data = df.copy()
            timeline_data['date_str'] = timeline_data['date'].dt.strftime('%Y-%m-%d')

            # Create stacked area chart
            fig = px.area(timeline_data, x='date', y=['goals', 'assists'],
                          title="Goal Contributions Over Time",
                          labels={'value': 'Count', 'variable': 'Type'},
                          color_discrete_map={'goals': 'rgba(39, 128, 227, 0.7)',
                                              'assists': 'rgba(39, 227, 128, 0.7)'},
                          hover_data=['date_str', 'session_type', 'position'])

            fig.update_layout(height=350, hovermode="x unified",
                              xaxis_title="Date", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)

        with right_col:
            # ===========================
            # Performance Heatmap
            # ===========================
            st.subheader("🔥 Performance Heatmap")

            # Prepare metrics for heatmap
            heatmap_metrics = ['goals', 'assists', 'tackles', 'passes_completed',
                               'crosses', 'shots_on_target', 'rating']

            # Calculate correlation matrix
            corr_matrix = df[heatmap_metrics].corr()

            # Create heatmap
            fig = px.imshow(
                corr_matrix,
                text_auto=True,
                color_continuous_scale='YlGnBu',
                title="Performance Metrics Correlation"
            )

            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

            # ===========================
            # Session Type Distribution - Donut Chart
            # ===========================
            st.subheader("🏃 Training Session Types")

            session_counts = df['session_type'].value_counts().reset_index()
            session_counts.columns = ['session_type', 'count']

            fig = px.pie(
                session_counts,
                values='count',
                names='session_type',
                title='Distribution of Session Types',
                hole=0.4
            )

            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=350, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            # ===========================
            # Session Duration vs Rating - Scatter Plot
            # ===========================
            st.subheader("⏱️ Duration vs Performance")

            fig = px.scatter(
                df,
                x='duration_mins',
                y='rating',
                color='session_type',
                size='goal_contributions',
                hover_data=['date', 'goals', 'assists', 'position'],
                title="Session Duration vs. Performance Rating",
                labels={'duration_mins': 'Duration (minutes)', 'rating': 'Performance Rating'}
            )

            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

        # ===========================
        # Defensive Performance
        # ===========================
        st.subheader("🛡️ Defensive Performance")

        # Filter out physical training for defensive stats
        match_df = df[df['position'] != "🏋️ Physical Only"]

        if not match_df.empty:
            # Create columns for defensive stats
            def_col1, def_col2 = st.columns(2)

            with def_col1:
                # Tackles by session type
                tackles_by_type = match_df.groupby('session_type')['tackles'].mean().reset_index()

                fig = px.bar(
                    tackles_by_type,
                    x='session_type',
                    y='tackles',
                    title="Average Tackles by Session Type",
                    color='session_type',
                    labels={'tackles': 'Avg. Tackles', 'session_type': 'Session Type'}
                )

                fig.update_layout(height=350, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            with def_col2:
                # Defensive metrics over time
                def_timeline = match_df.sort_values('date')
                def_timeline['month_year'] = def_timeline['date'].dt.strftime('%b %Y')

                monthly_defense = def_timeline.groupby('month_year').agg({
                    'tackles': 'mean',
                    'passes_completed': 'mean'
                }).reset_index()

                fig = px.line(
                    monthly_defense,
                    x='month_year',
                    y=['tackles', 'passes_completed'],
                    title="Defensive Metrics Over Time",
                    markers=True,
                    line_shape='spline',
                    labels={'value': 'Average', 'variable': 'Metric', 'month_year': 'Month'}
                )

                fig.update_layout(height=350, hovermode="x unified")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data to visualize defensive performance")

        # ===========================
        # Recent Progress Tracker - Last 10 Sessions
        # ===========================
        st.subheader("📊 Recent Progress Tracker (Last 10 Sessions)")

        recent_df = df.sort_values('date', ascending=False).head(10).sort_values('date')
        recent_df['session_num'] = range(1, len(recent_df) + 1)

        # Create columns for progress graphs
        prog_col1, prog_col2 = st.columns(2)

        with prog_col1:
            fig = px.line(
                recent_df,
                x='session_num',
                y='rating',
                title="Rating Progression",
                markers=True,
                text='rating',
                labels={'session_num': 'Session #', 'rating': 'Performance Rating'}
            )

            fig.update_traces(textposition="top center")
            fig.update_layout(height=350, yaxis_range=[min(recent_df['rating']) - 0.5, max(recent_df['rating']) + 0.5])
            st.plotly_chart(fig, use_container_width=True)

        with prog_col2:
            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=recent_df['session_num'],
                y=recent_df['goals'],
                name='Goals',
                marker_color='rgba(39, 128, 227, 0.7)'
            ))

            fig.add_trace(go.Bar(
                x=recent_df['session_num'],
                y=recent_df['assists'],
                name='Assists',
                marker_color='rgba(39, 227, 128, 0.7)'
            ))

            fig.update_layout(
                title="Recent Goal Contributions",
                xaxis_title="Session #",
                yaxis_title="Count",
                barmode='group',
                height=350
            )

            st.plotly_chart(fig, use_container_width=True)

        # ===========================
        # Physical Training Visualization
        # ===========================
        st.subheader("🏋️ Physical Training Analysis")
        physical_days = df[df['position'] == "🏋️ Physical Only"]

        if not physical_days.empty:
            st.write(f"Ethan had **{len(physical_days)}** Physical Training days 💪")

            # Create columns for physical training analysis
            phys_col1, phys_col2 = st.columns(2)

            with phys_col1:
                # Duration trend
                fig = px.line(
                    physical_days.sort_values('date'),
                    x='date',
                    y='duration_mins',
                    title="Physical Training Duration Trend",
                    markers=True,
                    labels={'date': 'Date', 'duration_mins': 'Duration (minutes)'}
                )

                fig.update_layout(height=350)
                st.plotly_chart(fig, use_container_width=True)

            with phys_col2:
                # Session type breakdown for physical training
                phys_types = physical_days['session_type'].value_counts().reset_index()
                phys_types.columns = ['session_type', 'count']

                fig = px.pie(
                    phys_types,
                    values='count',
                    names='session_type',
                    title='Physical Training Types',
                    hole=0.4
                )

                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=350, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

            # Display physical training details in expandable table
            with st.expander("View Physical Training Details", expanded=False):
                st.dataframe(physical_days[['date', 'session_type', 'duration_mins', 'comments']],
                             use_container_width=True)
        else:
            st.info("No physical training sessions recorded yet")

        # ===========================
        # Performance Insights - AI-Generated
        # ===========================
        st.subheader("🧠 Performance Insights")

        # Create insights based on the data
        insights = []

        # Check if there's enough data
        if len(df) >= 5:
            # Check form
            if rating_diff > 0.3:
                insights.append(
                    "🔥 **Great improvement in recent form!** Ethan's performance rating is trending upward.")
            elif rating_diff < -0.3:
                insights.append("📉 **Recent form has dipped.** Consider focusing on areas that need improvement.")

            # Position performance
            if not match_df.empty and len(match_df['position'].unique()) > 1:
                position_ratings = match_df.groupby('position')['rating'].mean().sort_values(ascending=False)
                best_pos = position_ratings.index[0]
                worst_pos = position_ratings.index[-1]

                insights.append(
                    f"⭐ Ethan performs best as a **{best_pos}** with an average rating of {position_ratings[0]:.2f}")

                if len(position_ratings) > 1:
                    insights.append(
                        f"💡 Consider improving performance as a **{worst_pos}** (current avg: {position_ratings[-1]:.2f})")

            # Check for session correlations
            if df['duration_mins'].corr(df['rating']) > 0.3:
                insights.append(
                    "⏱️ **Longer sessions correlate with better performance ratings.** The extra practice is paying off!")
            elif df['duration_mins'].corr(df['rating']) < -0.3:
                insights.append(
                    "⚠️ **Longer sessions may be causing fatigue.** Consider shorter, more focused sessions.")

            # Goal scoring trends
            recent_goals = df.tail(5)['goals'].sum()
            previous_goals = df.iloc[-10:-5]['goals'].sum() if len(df) >= 10 else 0

            if recent_goals > previous_goals * 1.2 and previous_goals > 0:
                insights.append("⚽ **Goal scoring is improving!** Recent sessions show increased finishing ability.")
            elif recent_goals < previous_goals * 0.8 and previous_goals > 0:
                insights.append("🎯 **Goal scoring has decreased recently.** Consider extra shooting practice.")

        # Display insights
        if insights:
            for insight in insights:
                st.markdown(insight)
        else:
            st.info("Add more training sessions to generate performance insights")

    except Exception as e:
        st.error(f"❌ Error rendering dashboard: {e}")
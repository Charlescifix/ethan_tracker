# ===========================
# Data Handler for PostgreSQL
# ===========================

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from models.training_session import TrainingSession
import streamlit as st

# Load env vars
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

# ===========================
# DB Connection
# ===========================
def get_connection():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        st.error(f"❌ DB connection failed: {e}")
        return None

# ===========================
# Create Table
# ===========================
def create_table():
    """
    Creates the training_sessions table if it does not already exist.
    """
    query = """
    CREATE TABLE IF NOT EXISTS training_sessions (
        id SERIAL PRIMARY KEY,
        date TIMESTAMP NOT NULL,
        session_type VARCHAR(50) NOT NULL,
        duration_mins INT NOT NULL,
        position VARCHAR(20) NULL,             -- Made nullable
        goals INT NOT NULL DEFAULT 0,
        assists INT NOT NULL DEFAULT 0,
        tackles INT NOT NULL DEFAULT 0,
        passes_completed INT NOT NULL DEFAULT 0,
        crosses INT NOT NULL DEFAULT 0,
        shots_on_target INT NOT NULL DEFAULT 0,
        rating INT NOT NULL,
        comments TEXT,
        created_at TIMESTAMP DEFAULT NOW(),
        UNIQUE(date, session_type)
    );
    """
    conn = get_connection()
    if conn:
        with conn.cursor() as cur:
            cur.execute(query)
            conn.commit()
        conn.close()
        print("✅ Table created or already exists.")

# ===========================
# Save Session with Uniqueness Check
# ===========================
def save_training_session(session: TrainingSession):
    """
    Saves a training session object to the database.
    Automatically sorts by date during insertion.
    """
    query = """
    INSERT INTO training_sessions (
        date, session_type, duration_mins, position, 
        goals, assists, tackles, passes_completed, 
        crosses, shots_on_target, rating, comments
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (date, session_type) DO NOTHING;
    """

    values = (
        session.date,
        session.session_type,
        session.duration_mins,
        session.position if session.position != "None" else None,  # Allow Null
        session.goals,
        session.assists,
        session.tackles,
        session.passes_completed,
        session.crosses,
        session.shots_on_target,
        session.rating,
        session.comments
    )

    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, values)
                if cur.rowcount == 0:
                    st.error("❌ Session already exists for this date and type.")
                else:
                    conn.commit()
                    st.success("✅ Session saved successfully.")
        except Exception as e:
            st.error(f"❌ Error saving session: {e}")
        finally:
            conn.close()

# ===========================
# Fetch Sessions
# ===========================
def fetch_all_sessions():
    """
    Fetches all training sessions from the database, ordered by date.
    """
    query = "SELECT * FROM training_sessions ORDER BY date DESC;"
    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
        except Exception as e:
            st.error(f"❌ Error fetching data: {e}")
        finally:
            conn.close()
    return []


# ===========================
# Delete Session
# ===========================
def delete_session(session_id):
    """
    Deletes a training session by its ID.

    Args:
        session_id (int): The ID of the session to delete

    Returns:
        bool: True if deletion was successful, False otherwise
    """
    query = "DELETE FROM training_sessions WHERE id = %s;"

    conn = get_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, (session_id,))
                conn.commit()
                if cur.rowcount > 0:
                    return True
                else:
                    st.warning("Session not found.")
                    return False
        except Exception as e:
            st.error(f"❌ Error deleting session: {e}")
            return False
        finally:
            conn.close()
    return False
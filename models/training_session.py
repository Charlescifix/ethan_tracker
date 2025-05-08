# ===========================
# Training Session Data Model
# ===========================

from datetime import datetime

class TrainingSession:
    """
    Data model representing a single training session or match.
    """
    def __init__(self,
                 date: datetime,
                 session_type: str,
                 duration_mins: int,
                 position: str,
                 goals: int,
                 assists: int,
                 tackles: int,
                 passes_completed: int,
                 crosses: int,
                 shots_on_target: int,
                 rating: int,
                 comments: str = ""):
        self.date = date
        self.session_type = session_type
        self.duration_mins = duration_mins
        self.position = position
        self.goals = goals
        self.assists = assists
        self.tackles = tackles
        self.passes_completed = passes_completed
        self.crosses = crosses
        self.shots_on_target = shots_on_target
        self.rating = rating
        self.comments = comments

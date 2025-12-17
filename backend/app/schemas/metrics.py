from pydantic import BaseModel


class MetricsResponse(BaseModel):
    total_entries: int
    current_streak: int
    longest_streak: int
    entries_this_week: int
    entries_this_month: int
    total_goals: int
    active_goals: int
    completed_goals: int

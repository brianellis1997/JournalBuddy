from datetime import datetime, timedelta
from typing import List, Tuple


def calculate_streak(entry_dates: List[datetime]) -> Tuple[int, int]:
    if not entry_dates:
        return 0, 0

    dates = sorted(set(d.date() for d in entry_dates), reverse=True)

    today = datetime.utcnow().date()
    current_streak = 0
    check_date = today

    for date in dates:
        if date == check_date:
            current_streak += 1
            check_date -= timedelta(days=1)
        elif date == check_date + timedelta(days=1):
            continue
        else:
            break

    longest_streak = 0
    streak = 0
    prev_date = None

    for date in sorted(dates):
        if prev_date is None or date == prev_date + timedelta(days=1):
            streak += 1
        else:
            longest_streak = max(longest_streak, streak)
            streak = 1
        prev_date = date

    longest_streak = max(longest_streak, streak)

    return current_streak, longest_streak

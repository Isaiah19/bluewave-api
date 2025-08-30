# app/services/timeutils.py
from datetime import datetime, timezone

def is_current_quarter(dt: datetime) -> bool:
    now = datetime.now(timezone.utc)
    q = (dt.month - 1) // 3
    q_now = (now.month - 1) // 3
    return dt.year == now.year and q == q_now


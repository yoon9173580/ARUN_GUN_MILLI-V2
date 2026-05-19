import pytz
from datetime import datetime

NY = pytz.timezone("America/New_York")

def get_time_window_score(now=None):
    if now is None:
        now = datetime.now(NY)
    
    hour = now.hour
    minute = now.minute
    current_time = f"{hour:02d}:{minute:02d}"

    if (10 <= hour < 11) or (hour == 10 and minute >= 30):           # 10:30~11:30
        score = 20
        emoji = "✅"
        window_name = "10:30–11:30 (Highest Priority Window)"
    elif (14 <= hour < 15) and minute < 45:                          # 14:00~14:45
        score = 20
        emoji = "✅"
        window_name = "14:00–14:45 (Gamma Window)"
    else:
        score = 0
        emoji = "❌"
        window_name = "Avoid — Waiting for Prime Window"

    return {
        "score": score,
        "emoji": emoji,
        "window": window_name,
        "current_time": current_time,
        "description": "0DTE에서 승률을 30% 이상 좌우하는 핵심 시간 창"
    }

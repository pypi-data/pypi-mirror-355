from datetime import datetime, timedelta

def format_time(dt: datetime, now: datetime = None) -> str:
    now = now or datetime.now()
    diff = now - dt

    if diff.total_seconds() < 60:
        return "just now"
    elif diff.total_seconds() < 3600:
        minutes = int(diff.total_seconds() / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif diff.total_seconds() < 86400:
        hours = int(diff.total_seconds() / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.total_seconds() < 172800:
        return f"yesterday at {dt.strftime('%-I:%M %p')}"
    elif diff.days < 7:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    else:
        return dt.strftime("%b %d, %Y at %-I:%M %p")
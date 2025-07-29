from datetime import datetime, timezone

def get_current_utc_timestamp():
    return datetime.now(timezone.utc).isoformat()

def format_datetime_iso(dt: datetime):
    return dt.replace(tzinfo=timezone.utc).isoformat()

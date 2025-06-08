# app/utils/common_helpers.py
from datetime import datetime, timezone
from typing import Optional, List, Any, Dict, Type, TypeVar


def get_utc_now() -> datetime:
    """Returns the current time in UTC with timezone information."""
    return datetime.now(timezone.utc)


def format_datetime_for_display(dt: Optional[datetime]) -> Optional[str]:
    """Formats a datetime object into a user-friendly string."""
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%d %H:%M:%S %Z")

# Add other common utility functions here as your project develops.
# For example:
# def generate_random_string(length: int = 10) -> str:
#     import random
#     import string
#     return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

# def parse_comma_separated_values(value: Optional[str]) -> List[str]:
#     if not value:
#         return []
#     return [item.strip() for item in value.split(',') if item.strip()]

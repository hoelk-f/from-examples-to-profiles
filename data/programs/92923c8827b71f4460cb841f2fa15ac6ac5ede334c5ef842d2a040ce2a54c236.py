import calendar

_months = set(calendar.month_abbr[1:])

def transform(x: str) -> str:
    parts = x.split()
    for i in range(len(parts) - 1):
        if parts[i].isdigit() and parts[i + 1] in _months:
            return f"{parts[i]} {parts[i + 1]}"
    return ""
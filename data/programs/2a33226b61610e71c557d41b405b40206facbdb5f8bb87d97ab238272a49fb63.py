def transform(x: str) -> str:
    parts = x.split(' ', 1)
    if len(parts) < 2:
        return ''
    month_part = parts[1]
    return month_part.split(',', 1)[0]
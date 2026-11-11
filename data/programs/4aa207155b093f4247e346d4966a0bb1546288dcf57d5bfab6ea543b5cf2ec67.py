def transform(x: str) -> str:
    parts = x.split(',')
    if len(parts) < 2:
        return ''
    lon = parts[1].replace('(longitude)', '').strip()
    return lon
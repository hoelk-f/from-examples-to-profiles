def transform(x: str) -> str:
    # Split after the first occurrence of ". "
    parts = x.split('. ', 1)
    if len(parts) < 2:
        return ''
    after = parts[1]
    # Take text before the first " -"
    result = after.split(' -', 1)[0]
    return result
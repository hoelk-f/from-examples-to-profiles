def transform(x: str) -> str:
    parts = x.split(',')
    if len(parts) >= 2:
        second = parts[1].strip()
        tokens = second.split()
        if tokens:
            return tokens[-1]
    return ""
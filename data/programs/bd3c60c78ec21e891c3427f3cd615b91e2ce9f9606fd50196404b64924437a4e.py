def transform(x: str) -> str:
    parts = x.split(",", 1)
    if len(parts) < 2:
        return ""
    after_comma = parts[1].lstrip()
    tokens = after_comma.split()
    return tokens[0] if tokens else ""
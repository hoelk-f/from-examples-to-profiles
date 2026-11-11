def transform(x: str) -> str:
    tokens = x.split()
    numeric_tokens = [t for t in tokens if t.isdigit()]
    if not numeric_tokens:
        return ""
    max_len = max(len(t) for t in numeric_tokens)
    for t in numeric_tokens:
        if len(t) == max_len:
            return t
    return ""
def transform(x: str) -> str:
    tokens = x.split()
    digit_tokens = [t for t in tokens if t.isdigit()]
    if not digit_tokens:
        return ""
    max_len = max(len(t) for t in digit_tokens)
    for t in digit_tokens:
        if len(t) == max_len:
            return t
    return ""
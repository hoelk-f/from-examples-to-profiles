def transform(x: str) -> str:
    tokens = x.split()
    numeric_tokens = [t for t in tokens if t.isdigit()]
    if not numeric_tokens:
        return ""
    return max(numeric_tokens, key=len)
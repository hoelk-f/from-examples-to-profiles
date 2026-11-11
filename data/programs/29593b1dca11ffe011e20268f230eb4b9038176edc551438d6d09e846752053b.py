def transform(x: str) -> str:
    tokens = x.split()
    numeric_tokens = [t for t in tokens if t.isdigit()]
    if not numeric_tokens:
        return ""
    # select the longest numeric token; if tie, the first encountered
    longest = max(numeric_tokens, key=lambda t: (len(t), -numeric_tokens.index(t)))
    return longest
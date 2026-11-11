def transform(x: str) -> str:
    tokens = x.split()
    digit_tokens = [t for t in tokens if t.isdigit()]
    return max(digit_tokens, key=len)

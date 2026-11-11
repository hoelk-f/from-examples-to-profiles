def transform(x: str) -> str:
    tokens = x.replace(';', ',').split(',')
    return max(tokens, key=len).strip()

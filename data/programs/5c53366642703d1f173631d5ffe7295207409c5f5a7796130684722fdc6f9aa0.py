def transform(x: str) -> str:
    tokens = x.split()
    max_len = -1
    max_idx = -1
    for i, t in enumerate(tokens):
        if t.isdigit():
            if len(t) > max_len:
                max_len = len(t)
                max_idx = i
    if 0 <= max_idx < len(tokens) - 1:
        return tokens[max_idx + 1]
    return ""
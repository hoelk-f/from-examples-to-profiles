def transform(x: str) -> str:
    count = 0
    for i, ch in enumerate(x):
        if ch == '.':
            count += 1
            if count == 2:
                return x[i + 1 :]
    return ""
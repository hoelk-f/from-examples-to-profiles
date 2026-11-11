def transform(x: str) -> str:
    parts = x.split()
    result = []
    for token in parts:
        if ',' in token:
            break
        result.append(token)
    return ' '.join(result)
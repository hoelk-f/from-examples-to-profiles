def transform(x: str) -> str:
    parts = []
    for p in x.split('.'):
        if p:
            parts.append(p)
            if len(parts) == 2:
                break
    return '.'.join(parts)
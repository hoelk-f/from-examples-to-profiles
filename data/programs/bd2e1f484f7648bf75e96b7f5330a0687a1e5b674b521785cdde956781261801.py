def transform(x: str) -> str:
    parts = x.split()
    kept = []
    for token in parts:
        if ',' in token:
            break
        kept.append(token)
    return ' '.join(kept)
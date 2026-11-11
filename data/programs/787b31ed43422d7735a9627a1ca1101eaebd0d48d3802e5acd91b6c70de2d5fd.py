def transform(x: str) -> str:
    tokens = x.split()
    candidates = [t for t in tokens if t.isdigit() and len(t) == 3]
    if len(candidates) == 1:
        return candidates[0]
    from collections import Counter
    cnt = Counter(tokens)
    for t in candidates:
        if cnt[t] == 1:
            return t
    # fallback: return first candidate if exists, else empty string
    return candidates[0] if candidates else ""
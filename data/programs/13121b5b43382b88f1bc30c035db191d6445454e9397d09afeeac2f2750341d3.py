def transform(x: str) -> str:
    import re
    m = re.search(r'\((\d+)(?:\s+years?\s+old)?\)', x)
    if m:
        return m.group(1)
    # fallback: extract first number
    m = re.search(r'\d+', x)
    return m.group(0) if m else ''
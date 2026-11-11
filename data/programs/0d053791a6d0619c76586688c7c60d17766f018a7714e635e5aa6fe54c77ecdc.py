def transform(x: str) -> str:
    import re
    return re.sub(r'\s*\(\d+\)\s*$', '', x)
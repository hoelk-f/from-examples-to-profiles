def transform(x: str) -> str:
    import re
    parts = re.split(r'\n|/n', x)
    parts = [p for p in parts if p]
    return parts[-1] if parts else ""
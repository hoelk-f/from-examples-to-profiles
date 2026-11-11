def transform(x: str) -> str:
    parts = x.split('.')
    if parts and parts[-1] == '':
        parts = parts[:-1]
    return '.'.join(parts[:2])
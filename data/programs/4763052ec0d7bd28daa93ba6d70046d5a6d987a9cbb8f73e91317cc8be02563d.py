def transform(x: str) -> str:
    parts = x.split()
    if len(parts) < 2:
        return ""
    time_part = parts[1]
    components = time_part.split(":")
    if len(components) < 2:
        return ""
    return components[1]
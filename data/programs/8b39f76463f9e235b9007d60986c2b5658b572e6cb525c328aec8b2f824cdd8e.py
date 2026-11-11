def transform(x: str) -> str:
    for part in x.split():
        if part.isdigit() and len(part) == 4:
            return part
    return ""

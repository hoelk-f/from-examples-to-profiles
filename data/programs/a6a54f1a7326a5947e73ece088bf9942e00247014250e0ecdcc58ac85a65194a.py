def transform(x: str) -> str:
    # Extract the part after the first ". " and before the first " - "
    parts = x.split('. ', 1)
    after_dot = parts[1] if len(parts) > 1 else x
    first_part = after_dot.split(' - ', 1)[0]
    return first_part.strip()
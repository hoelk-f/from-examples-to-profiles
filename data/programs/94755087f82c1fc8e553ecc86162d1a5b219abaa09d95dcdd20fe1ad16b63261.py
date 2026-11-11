def transform(x: str) -> str:
    # Remove leading part up to the first ". "
    _, sep, rest = x.partition('. ')
    if sep:
        candidate = rest
    else:
        candidate = x
    # Take portion before the first " - "
    before_dash, sep2, _ = candidate.partition(' - ')
    result = before_dash.strip()
    return result
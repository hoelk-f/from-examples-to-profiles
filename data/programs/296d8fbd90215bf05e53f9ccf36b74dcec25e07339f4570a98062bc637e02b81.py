def transform(x: str) -> str:
    """
    Extract the US state abbreviation from an address string.
    Assumes the state abbreviation appears as a two‑letter token
    before the ZIP code, typically after the last comma.
    """
    # Split on commas, take the last segment (city, state ZIP)
    last_part = x.rsplit(",", 1)[-1].strip()
    # The state is the first token in this segment
    state = last_part.split()[0]
    return state.upper()
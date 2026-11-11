def transform(x: str) -> str:
    """
    Extracts the middle numeric block from a phone-number-like string.
    Example: "+132 313-075-754" -> "075"
    """
    # Split off any leading part before the first space (e.g., country code)
    parts = x.split()
    if len(parts) < 2:
        # No space found; fallback to whole string
        candidate = x
    else:
        candidate = parts[1]

    # Split the candidate by hyphens and return the second segment if possible
    groups = candidate.split('-')
    if len(groups) >= 3:
        return groups[1]
    # Fallback: return empty string if pattern not matched
    return ""
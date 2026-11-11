def transform(x: str) -> str:
    """
    Extract the province abbreviation from an Italian address string.
    The address is expected to end with ", Italy" and contain a
    two‑letter province code just before that suffix.
    """
    # Remove the trailing ", Italy" if present
    if x.endswith(", Italy"):
        x = x[: -len(", Italy")]
    # Strip any surrounding whitespace
    x = x.strip()
    # The province code is the last whitespace‑separated token
    parts = x.split()
    if not parts:
        return ""
    return parts[-1]
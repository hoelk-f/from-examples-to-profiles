def transform(x: str) -> str:
    # Remove leading index and dot
    _, _, remainder = x.partition('. ')
    # If partition failed, use the whole string
    if not remainder:
        remainder = x
    # Remove trailing price part starting with ", $"
    title = remainder.rsplit(', $', 1)[0]
    return title
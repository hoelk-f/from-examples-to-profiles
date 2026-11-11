def transform(x: str) -> str:
    """
    Extracts the substring after the last comma within angle brackets.
    Example:
        "USD.EUR<IDEALPRO,CASH,USD>" -> "USD"
    """
    # Find the content inside '<' and '>'
    start = x.find('<')
    end = x.find('>', start)
    if start == -1 or end == -1:
        return ""
    inner = x[start + 1:end]
    # Split by commas and return the last element
    parts = inner.split(',')
    return parts[-1] if parts else ""
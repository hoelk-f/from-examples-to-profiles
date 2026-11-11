def transform(x: str) -> str:
    # Expect ISO 8601 date-time string like "YYYY-MM-DDThh:mm:ssZ"
    # Return the day component (two digits)
    if len(x) >= 10:
        return x[8:10]
    return ""
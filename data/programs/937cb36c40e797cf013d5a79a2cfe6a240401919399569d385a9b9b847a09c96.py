def transform(x: str) -> str:
    # Split the date part from the time part
    date_part = x.split()[0]
    # Split the date into day, month, year
    parts = date_part.split('-')
    # Return the year component
    return parts[2] if len(parts) > 2 else ""
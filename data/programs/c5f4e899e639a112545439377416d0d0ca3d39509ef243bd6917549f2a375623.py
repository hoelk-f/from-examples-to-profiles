def transform(x: str) -> str:
    # Split the string into date and time parts, then extract seconds
    time_part = x.split()[1]
    return time_part.split(":")[2]
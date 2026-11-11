def transform(x: str) -> str:
    time_part = x.split(" ")[1]
    return time_part.split(":")[1]

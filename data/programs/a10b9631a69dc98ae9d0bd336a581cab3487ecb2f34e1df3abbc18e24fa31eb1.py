def transform(x: str) -> str:
    tokens = x.split()
    months = {"Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"}
    for i in range(len(tokens) - 1):
        day, month = tokens[i], tokens[i + 1]
        if day.isdigit() and month in months:
            return f"{day} {month}"
    return ""
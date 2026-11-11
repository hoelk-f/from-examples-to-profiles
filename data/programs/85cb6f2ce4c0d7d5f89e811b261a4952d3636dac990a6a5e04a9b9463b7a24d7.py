def transform(x: str) -> str:
    months = {
        "jan", "feb", "mar", "apr", "may", "jun",
        "jul", "aug", "sep", "oct", "nov", "dec"
    }
    parts = x.split()
    for i in range(len(parts) - 1):
        if parts[i].isdigit() and parts[i + 1][:3].lower() in months:
            return f"{parts[i]} {parts[i + 1]}"
    return ""
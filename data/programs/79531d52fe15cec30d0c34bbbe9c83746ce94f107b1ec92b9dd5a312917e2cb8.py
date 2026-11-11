def transform(x: str) -> str:
    titles = {
        "Mr", "Mrs", "Ms", "Miss", "Dr", "Prof", "Professor",
        "Sir", "Madam", "Mx", "Lord", "Lady"
    }
    parts = x.split()
    if not parts:
        return x
    first = parts[0]
    # Remove trailing period for titles like "Dr."
    core = first.rstrip(".")
    if core in titles:
        return " ".join(parts[1:])
    return x
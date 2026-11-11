def transform(x: str) -> str:
    import re
    tokens = x.split()
    if not tokens:
        return ""
    # Skip the first token (assumed to be a number or identifier)
    tokens = tokens[1:]
    name_parts = []
    year_range_pattern = re.compile(r"^\d{4}-\d{4}$")
    for token in tokens:
        if year_range_pattern.match(token):
            break
        name_parts.append(token)
    return " ".join(name_parts)
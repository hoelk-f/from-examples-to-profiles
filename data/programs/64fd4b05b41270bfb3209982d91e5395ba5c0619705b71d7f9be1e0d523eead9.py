import re

def transform(x: str) -> str:
    parts = x.split()
    # Skip the first part (e.g., an index)
    name_parts = []
    for token in parts[1:]:
        if re.fullmatch(r"\d{4}-\d{4}", token):
            break
        name_parts.append(token)
    return " ".join(name_parts)
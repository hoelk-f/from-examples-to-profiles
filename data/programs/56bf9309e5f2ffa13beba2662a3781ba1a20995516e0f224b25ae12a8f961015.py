import re

def transform(x: str) -> str:
    tokens = x.split()
    name_parts = []
    year_regex = re.compile(r'^\d{4}-\d{4}$')
    for token in tokens[1:]:
        if year_regex.match(token):
            break
        name_parts.append(token)
    return " ".join(name_parts)
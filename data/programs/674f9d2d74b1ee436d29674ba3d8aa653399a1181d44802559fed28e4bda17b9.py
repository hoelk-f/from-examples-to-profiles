import re

def transform(x: str) -> str:
    groups = re.findall(r'\d{3}', x)
    return groups[2] if len(groups) > 2 else ''
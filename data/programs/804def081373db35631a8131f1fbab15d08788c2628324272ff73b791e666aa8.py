import re

def transform(x: str) -> str:
    match = re.search(r'([-\d.]+)\(longitude\)', x)
    return match.group(1)

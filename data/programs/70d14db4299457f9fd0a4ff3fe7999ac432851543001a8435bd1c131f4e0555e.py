import re

def transform(x: str) -> str:
    m = re.search(r'([-+]?\d+\.?\d*)\(longitude\)', x)
    return m.group(1)

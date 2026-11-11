import re

def transform(x: str) -> str:
    m = re.search(r'([+-]?\d+(?:\.\d+)?)\s*\(longitude\)', x)
    if m:
        return m.group(1)
    parts = x.split(',')
    if len(parts) > 1:
        part = parts[1].split('(')[0].strip()
        return part
    return ""
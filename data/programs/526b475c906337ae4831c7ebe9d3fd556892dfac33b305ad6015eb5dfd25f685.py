import re

def transform(x: str) -> str:
    matches = re.findall(r'\[\[([^]]+)\]\]', x)
    if not matches:
        return ""
    last = matches[-1]
    # If there is a pipe, take the part after the last pipe
    if '|' in last:
        return last.split('|')[-1]
    return last
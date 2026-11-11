import re

def transform(x: str) -> str:
    matches = re.findall(r'\[\[([^\]]+)\]\]', x)
    last = matches[-1]
    if '|' in last:
        return last.split('|')[-1]
    return last

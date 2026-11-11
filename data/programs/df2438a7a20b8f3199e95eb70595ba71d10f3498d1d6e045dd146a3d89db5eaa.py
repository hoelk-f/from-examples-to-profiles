import re

def transform(x: str) -> str:
    m = re.search(r'\[\[.*?\|(.*?)\]\]', x)
    if m:
        return m.group(1)
    # fallback: return content of first [[...]] if no pipe
    m = re.search(r'\[\[(.*?)\]\]', x)
    return m.group(1) if m else ""
import re

def transform(x: str) -> str:
    # Split on en dash (–) which separates actor and film; fallback to whole string
    parts = x.split('–', 1)
    segment = parts[1] if len(parts) > 1 else x
    # Find first wiki link [[...]]
    m = re.search(r'\[\[(.+?)\]\]', segment)
    if not m:
        return ""
    content = m.group(1)
    # If link has a pipe, take the displayed part after the last pipe
    if '|' in content:
        content = content.split('|')[-1]
    return content.strip()

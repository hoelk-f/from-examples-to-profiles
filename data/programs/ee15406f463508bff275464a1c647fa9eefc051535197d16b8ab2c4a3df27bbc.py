import re

def transform(x: str) -> str:
    # Consider the part after the dash (en dash or hyphen)
    parts = re.split(r"[–-]", x, maxsplit=1)
    after_dash = parts[1] if len(parts) > 1 else x
    # Find the first [[...]] occurrence
    m = re.search(r"\[\[([^]]+)\]\]", after_dash)
    if not m:
        return ""
    content = m.group(1)
    # If there is a pipe, take the text after the last pipe
    if "|" in content:
        content = content.split("|")[-1]
    return content.strip()

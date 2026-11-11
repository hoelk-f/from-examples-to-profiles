import re

def transform(x: str) -> str:
    # Try to find a link enclosed in double single quotes and double brackets
    m = re.search(r"''\[\[(.*?)\]\]''", x)
    if not m:
        # Fallback to any double-bracket link
        m = re.search(r"\[\[(.*?)\]\]", x)
    if not m:
        return ""
    inner = m.group(1)
    # If the link contains a pipe, the displayed text follows the last pipe
    title = inner.split("|")[-1]
    return title.strip()
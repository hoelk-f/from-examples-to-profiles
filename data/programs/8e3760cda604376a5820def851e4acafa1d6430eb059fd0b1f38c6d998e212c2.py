import re

def transform(x: str) -> str:
    """
    Extracts the film title from a Wikipedia‑style markup string.
    Looks for the first occurrence of ''[[...]]'' and returns the
    displayed text of the link (after a pipe if present).
    """
    m = re.search(r"''\[\[(.*?)\]\]''", x)
    if not m:
        return ""
    link = m.group(1)
    # If there is a pipe, the part after it is the display text.
    if "|" in link:
        link = link.split("|", 1)[1]
    return link.strip()
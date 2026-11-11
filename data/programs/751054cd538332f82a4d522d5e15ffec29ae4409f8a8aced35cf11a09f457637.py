import re

def transform(x: str) -> str:
    """
    Extracts the display text of the first Wikipedia link that appears inside
    double single quotes, e.g. ''[[Some title|Display]]'' → "Display".
    """
    match = re.search(r"''\[\[[^\]|]*\|([^]]+)\]\]''", x)
    if match:
        return match.group(1)
    # fallback: try to find any [[...|...]] pattern without surrounding quotes
    match = re.search(r"\[\[[^\]|]*\|([^]]+)\]\]", x)
    if match:
        return match.group(1)
    return ""
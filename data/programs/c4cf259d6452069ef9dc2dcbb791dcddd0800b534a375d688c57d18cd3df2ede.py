import re

def transform(x: str) -> str:
    """
    Extracts the displayed title from a MediaWiki style link that is wrapped in double single quotes.
    Example:
        "** [[Meena Kumari]] – ''[[Azaad (1955 film)|Azaad]]'' as Shobha"
        → "Azaad"
    """
    # Find the first occurrence of ''[[...]]''
    match = re.search(r"''\[\[(.*?)\]\]''", x)
    if not match:
        return ""
    inner = match.group(1)
    # If there is a pipe, the part after the pipe is the displayed title.
    if "|" in inner:
        return inner.split("|", 1)[1].strip()
    # Otherwise return the whole inner content (trim whitespace)
    return inner.strip()
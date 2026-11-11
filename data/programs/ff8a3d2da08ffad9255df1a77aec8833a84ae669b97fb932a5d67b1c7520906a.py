import re

def transform(x: str) -> str:
    """
    Extracts the display text of the first MediaWiki link of the form [[...|display]].
    Returns an empty string if no such link is found.
    """
    match = re.search(r'\[\[[^\]|]*\|([^]]+)\]\]', x)
    return match.group(1).strip() if match else ""
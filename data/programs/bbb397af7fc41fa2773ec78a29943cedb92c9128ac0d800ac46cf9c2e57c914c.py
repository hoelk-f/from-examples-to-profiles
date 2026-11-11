import re

def transform(x: str) -> str:
    """
    Extracts and returns the display text of the first wikilink that contains a pipe.
    Example:
        "** [[Meena Kumari]] – ''[[Azaad (1955 film)|Azaad]]'' as Shobha"
        -> "Azaad"
    """
    match = re.search(r'\[\[[^\]|]*\|([^]]+)\]\]', x)
    return match.group(1) if match else ""
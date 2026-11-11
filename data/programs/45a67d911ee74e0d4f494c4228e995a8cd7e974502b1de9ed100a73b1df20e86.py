import re

def transform(x: str) -> str:
    """
    Extracts the display text of the first wikilink that uses a pipe syntax.
    Example:
        "** [[Meena Kumari]] – ''[[Azaad (1955 film)|Azaad]]'' as Shobha"
        -> "Azaad"
    """
    # Search for a wikilink with a pipe, e.g., [[something|display]]
    m = re.search(r"\[\[([^|\]]+)\|([^]]+)\]\]", x)
    if m:
        return m.group(2).strip()
    # Fallback: if there is a wikilink without a pipe, return its target
    m = re.search(r"\[\[([^]]+)\]\]", x)
    if m:
        return m.group(1).strip()
    # If nothing matches, return the original string stripped
    return x.strip()
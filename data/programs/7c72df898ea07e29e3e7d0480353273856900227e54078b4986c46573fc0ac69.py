import re

def transform(x: str) -> str:
    """
    Extracts the display text of the first Wikipedia link that appears
    within double single quotes (''...''), typically used for film titles.
    If the link contains a pipe, the text after the pipe is returned;
    otherwise the whole link text is returned. Returns an empty string
    if no such pattern is found.
    """
    # Pattern for ''[[Link|Display]]'' or ''[[Display]]''
    pattern = re.compile(r"''\[\[([^|\]]+)\|([^]]+)\]\]''|''\[\[([^|\]]+)\]\]''")
    match = pattern.search(x)
    if not match:
        return ""
    # If the first alternative matched, group 2 is the display text.
    if match.group(2) is not None:
        return match.group(2)
    # Otherwise, group 3 is the whole link text.
    return match.group(3)
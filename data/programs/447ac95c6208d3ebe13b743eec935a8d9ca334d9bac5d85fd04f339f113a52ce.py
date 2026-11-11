import re

def transform(x: str) -> str:
    # Find all wikilink contents [[...]]
    links = [m.group(1) for m in re.finditer(r'\[\[(.*?)\]\]', x)]
    if len(links) < 2:
        return ""
    # Take the second link (movie title)
    title_part = links[1]
    # If the link contains a pipe, the displayed text is after the last pipe
    if '|' in title_part:
        title_part = title_part.split('|')[-1]
    return title_part.strip()
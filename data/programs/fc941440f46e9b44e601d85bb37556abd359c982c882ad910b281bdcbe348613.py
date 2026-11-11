import re

def transform(x: str) -> str:
    # Find the dash that separates the actor from the film
    dash_pos = x.find('–')
    if dash_pos == -1:
        dash_pos = x.find('-')
    # Consider the part after the dash; if no dash, use whole string
    after_dash = x[dash_pos + 1:] if dash_pos != -1 else x
    # Find the first wiki link [[...]] after the dash
    m = re.search(r'\[\[([^|\]]+)(?:\|([^]]+))?\]\]', after_dash)
    if not m:
        return ""
    # Return the display text if present, otherwise the link target
    return m.group(2) if m.group(2) is not None else m.group(1)
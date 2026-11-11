import re

def transform(x: str) -> str:
    s = x.strip()
    # Remove trailing parenthetical part if present
    paren_idx = s.find('(')
    if paren_idx != -1:
        s = s[:paren_idx].strip()
    # Remove leading number(s) and following whitespace
    s = re.sub(r'^\d+\s+', '', s)
    return s
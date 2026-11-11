import re

def transform(x: str) -> str:
    tokens = [t.strip() for t in re.split(r'[;,]', x) if t.strip()]
    if not tokens:
        return ''
    return max(tokens, key=lambda t: (len(t), -tokens.index(t)))  # longest, first occurrence in tie
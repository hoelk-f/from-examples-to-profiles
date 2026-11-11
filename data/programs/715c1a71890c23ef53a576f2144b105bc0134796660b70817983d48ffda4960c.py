import re

def transform(x: str) -> str:
    # Remove leading digits and any following whitespace
    s = re.sub(r'^\d+\s*', '', x)
    # Remove trailing whitespace and parenthesized part (e.g., " (BEL)")
    s = re.sub(r'\s*\([^)]*\)\s*$', '', s)
    return s
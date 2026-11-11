import re

def transform(x: str) -> str:
    """
    Remove a leading integer and trailing country code in parentheses.
    Example: "5 Eddy Merckx (BEL)" -> "Eddy Merckx"
    """
    # Strip whitespace
    s = x.strip()
    # Try regex pattern
    m = re.match(r'^\d+\s+(.+?)\s*\([A-Z]{3}\)$', s)
    if m:
        return m.group(1).strip()
    # Fallback: remove leading number and trailing parentheses content
    # Remove leading number
    parts = s.split(maxsplit=1)
    if len(parts) == 2 and parts[0].isdigit():
        s = parts[1]
    # Remove trailing parentheses part
    if '(' in s:
        s = s[:s.rfind('(')].strip()
    return s.strip()

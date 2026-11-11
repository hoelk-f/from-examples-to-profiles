import re

def transform(x: str) -> str:
    """
    Extracts the name from a string formatted as:
    "<number> <name> <year-range> <party>"
    """
    m = re.search(r'^\d+\s+(.+?)\s+\d{4}-\d{4}\b', x)
    if m:
        return m.group(1).strip()
    # Fallback: return the original string if pattern not found
    return x.strip()
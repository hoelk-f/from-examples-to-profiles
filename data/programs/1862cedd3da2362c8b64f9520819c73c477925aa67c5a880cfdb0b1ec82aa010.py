import re

def transform(x: str) -> str:
    # Extract the header name inside <> or "" if present
    m = re.search(r'<([^>]+)>', x)
    if not m:
        m = re.search(r'["\']([^"\']+)["\']', x)
    header = m.group(1) if m else x
    # Return the part before the first dot
    return header.split('.')[0]
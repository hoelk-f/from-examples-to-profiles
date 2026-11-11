def transform(x: str) -> str:
    start = x.find('<')
    end = x.find('>', start + 1)
    if start == -1 or end == -1:
        # fallback: try quotes
        start = x.find('"')
        end = x.find('"', start + 1)
        if start == -1 or end == -1:
            return ""
    name = x[start + 1:end]
    # Remove extension if present (e.g., .h, .hpp, .hh, etc.)
    if '.' in name:
        name = name.split('.')[0]
    return name
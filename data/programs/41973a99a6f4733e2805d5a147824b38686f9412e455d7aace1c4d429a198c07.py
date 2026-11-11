def transform(x: str) -> str:
    import re
    # Try to get the token after "OS "
    if "OS " in x:
        after = x.split("OS ", 1)[1]
        token = after.split()[0]
        if re.fullmatch(r"\d+(?:\.\d+)+", token):
            return token
    # Fallback: first occurrence of a version-like pattern
    m = re.search(r"\d+(?:\.\d+)+", x)
    return m.group(0) if m else ""
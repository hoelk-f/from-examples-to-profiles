def transform(x: str) -> str:
    import re
    m = re.search(r"<([^>]+)>", x)
    if not m:
        return ""
    name = m.group(1)
    if "." in name:
        name = name.split(".", 1)[0]
    return name
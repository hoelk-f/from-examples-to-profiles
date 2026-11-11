def transform(x: str) -> str:
    import re

    # split on an en‑dash or a hyphen surrounded by spaces
    if "–" in x:
        parts = x.split("–", 1)
    else:
        parts = x.split("-", 1)

    right = parts[1] if len(parts) > 1 else x

    # find the first wikilink in the right‑hand side
    m = re.search(r"\[\[([^|\]]+)(?:\|([^|\]]+))?\]\]", right)
    if not m:
        return ""

    # use the displayed text if present, otherwise the target title
    return m.group(2) if m.group(2) is not None else m.group(1)
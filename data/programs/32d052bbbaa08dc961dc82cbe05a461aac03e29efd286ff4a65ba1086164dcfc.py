def transform(x: str) -> str:
    # Split on en‑dash or hyphen to isolate the part after the actor name
    if '–' in x:
        parts = x.split('–', 1)
    else:
        parts = x.split('-', 1)
    if len(parts) < 2:
        return ''
    after = parts[1]

    # Find the first wiki link [[...]]
    start = after.find('[[')
    end = after.find(']]', start + 2) if start != -1 else -1
    if start == -1 or end == -1:
        return ''

    link = after[start + 2:end]

    # If the link contains a pipe, the displayed title is after the pipe
    title = link.split('|', 1)[1] if '|' in link else link

    # Strip surrounding whitespace and possible wiki markup quotes
    title = title.strip().strip("'").strip('"')
    return title
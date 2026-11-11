def transform(x: str) -> str:
    # Take the part before the first space (the phone number)
    phone_part = x.split(' ', 1)[0]
    # Split by hyphens and drop the first segment
    parts = phone_part.split('-')
    if len(parts) <= 1:
        return ''
    return '-'.join(parts[1:])
def transform(x: str) -> str:
    # Extract the part before any space (the phone number)
    phone = x.split()[0]
    parts = phone.split('-')
    # Return the last two segments joined by a hyphen
    return '-'.join(parts[1:])
def transform(x: str) -> str:
    # Extract the part before any whitespace (the phone-like segment)
    phone_part = x.split()[0]
    # Return everything after the first hyphen
    return phone_part.split('-', 1)[1]
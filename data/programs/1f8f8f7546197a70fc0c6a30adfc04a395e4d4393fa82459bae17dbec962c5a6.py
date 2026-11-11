def transform(x: str) -> str:
    # Remove the leading numbered prefix (e.g., "01. ")
    after_prefix = x.split('. ', 1)[-1]
    # Take the segment before the hyphen separator
    main_part = after_prefix.split(' -', 1)[0]
    return main_part.strip()

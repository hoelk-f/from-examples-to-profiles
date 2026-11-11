def transform(x: str) -> str:
    # Take the part before ", Italy"
    main_part = x.split(", Italy")[0].strip()
    # Return the last whitespace-separated token
    return main_part.split()[-1] if main_part else ""
def transform(x: str) -> str:
    # Remove the trailing ", Italy" if present
    main_part = x.split(", Italy")[0]
    # Split the remaining part by whitespace and return the last token
    tokens = main_part.strip().split()
    return tokens[-1] if tokens else ""
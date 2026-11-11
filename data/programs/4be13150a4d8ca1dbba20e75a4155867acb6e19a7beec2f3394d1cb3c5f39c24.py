def transform(x: str) -> str:
    for token in x.split():
        # skip tokens that are only digits (e.g., street numbers)
        if token.isdigit():
            continue
        # first token containing a letter is the target
        if any(c.isalpha() for c in token):
            return token.rstrip('.,;:!?')
    return ""
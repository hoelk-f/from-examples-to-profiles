def transform(x: str) -> str:
    """
    Extracts the leftmost label of the domain part of an email address.
    Example: "user@sub.example.com" -> "sub"
    """
    try:
        domain = x.split("@", 1)[1]
    except IndexError:
        return ""
    return domain.split(".", 1)[0]
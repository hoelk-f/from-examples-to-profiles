def transform(x: str) -> str:
    """
    Extracts the substring before the first dot in the local-part of an email address.
    Example: "John.Doe@example.com" -> "John"
    """
    # Split off the domain part
    local = x.split("@", 1)[0]
    # Return the portion before the first dot, or the whole local part if no dot exists
    return local.split(".", 1)[0]
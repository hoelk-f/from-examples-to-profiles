def transform(x: str) -> str:
    """
    Remove a leading honorific title from the input string, if present.
    """
    titles = {
        "Mr", "Mrs", "Ms", "Miss", "Dr", "Prof", "Professor", "Sir", "Madam",
        "Lady", "Lord", "Captain", "Capt", "Rev", "Father", "Fr", "Sr", "Sra",
        "Mister", "Madame", "Dame", "Hon", "Honorable", "Judge", "Justice",
        "President", "Prime", "PrimeMinister", "Governor", "Senator", "Mayor"
    }

    parts = x.split()
    if not parts:
        return x

    first = parts[0].rstrip('.')
    if first in titles:
        return " ".join(parts[1:])
    return x
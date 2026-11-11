def transform(x: str) -> str:
    titles = {
        "Mr", "Mrs", "Ms", "Miss", "Dr", "Prof", "Professor", "Sir", "Madam",
        "Lord", "Lady", "Captain", "Chief", "President", "Vice", "Vice-President",
        "Hon", "Honorable", "Judge", "Justice", "Senator", "Governor", "Rev",
        "Reverend", "Father", "Mother", "Brother", "Sister", "Master", "Mistress",
        "Dame", "Baron", "Baroness", "Count", "Countess", "Duke", "Duchess",
        "Earl", "Marquis", "Marquess", "Viscount", "Viscountess"
    }
    parts = x.split()
    if parts and parts[0] in titles:
        return " ".join(parts[1:])
    return x
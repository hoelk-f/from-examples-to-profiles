def transform(x: str) -> str:
    titles = {
        "Mr", "Mrs", "Ms", "Miss", "Dr", "Prof", "Professor",
        "Sir", "Madam", "Mx", "Lord", "Lady", "Captain", "Major",
        "Colonel", "General", "Rev", "Father", "Sister", "Brother",
        "Judge", "President", "Prime", "Minister", "Honorable",
        "Hon.", "Senator", "Sen.", "Representative", "Rep.", "Governor",
        "Mayor", "Dean", "Chancellor", "Principal", "Coach", "Officer",
        "Agent", "Chief", "Commander", "Captain", "Admiral"
    }
    words = x.split()
    while words and words[0].rstrip('.').title() in titles:
        words.pop(0)
    return " ".join(words)
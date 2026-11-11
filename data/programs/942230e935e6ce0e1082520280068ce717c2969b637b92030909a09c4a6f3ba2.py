def transform(x: str) -> str:
    # Split at the first comma to separate house number from the rest
    if ',' not in x:
        return x.strip()
    house_part, rest = x.split(',', 1)
    house_part = house_part.strip()
    rest = rest.strip()
    # Collect words until a numeric token (postal code) is encountered
    street_words = []
    for word in rest.split():
        if word.isdigit():
            break
        street_words.append(word)
    return f"{house_part}, " + " ".join(street_words)
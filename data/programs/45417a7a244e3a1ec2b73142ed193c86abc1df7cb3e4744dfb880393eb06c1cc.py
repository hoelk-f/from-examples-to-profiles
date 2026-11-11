def transform(x: str) -> str:
    return x[x.index("<price>") + 7 : x.index("</price>")]

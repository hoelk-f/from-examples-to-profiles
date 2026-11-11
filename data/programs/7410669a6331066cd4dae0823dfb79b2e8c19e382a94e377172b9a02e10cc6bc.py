import re

def transform(x: str) -> str:
    # Find the dash that separates actor from film
    dash_pos = x.find('–')
    if dash_pos == -1:
        dash_pos = x.find('-')
    after_dash = x[dash_pos + 1:] if dash_pos != -1 else x

    # Locate the first wiki link after the dash
    link_match = re.search(r'\[\[.*?\]\]', after_dash)
    if not link_match:
        return ""

    link_content = link_match.group(0)[2:-2]  # strip [[ and ]]
    # If there is a pipe, take the displayed text after it
    if '|' in link_content:
        link_content = link_content.split('|')[-1]

    return link_content.strip()
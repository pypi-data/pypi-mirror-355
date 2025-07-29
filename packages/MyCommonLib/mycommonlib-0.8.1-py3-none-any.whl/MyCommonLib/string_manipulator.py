from re import sub


def snake_case(s: str) -> str:
    """Convert a string to snake_case"""
    return '_'.join(
        sub('([A-Z][a-z]+)', r' \1',
            sub('([A-Z]+)', r' \1',
                s.replace('-', ' '))).split()).lower()


def camel_case(s: str) -> str:
    """Convert a string to camelCase"""
    s = sub(r"(_|-)+", " ", s).title().replace(" ", "")
    return ''.join([s[0].lower(), s[1:]])


def sentence_case(s: str) -> str:
    """Convert a string to Sentence case"""
    return sub(r"(_|-)+", " ", s).title()

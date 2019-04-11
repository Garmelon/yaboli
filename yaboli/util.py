import re

__all__ = ["mention", "atmention", "normalize", "similar", "plural"]

# Name/nick related functions

def mention(nick: str, ping: bool = False) -> str:
    mentioned = re.sub(r"""[,.!?;&<'"\s]""", "", nick)
    return "@" + mentioned if ping else mentioned

def atmention(nick: str) -> str:
    return mention(nick, ping=True)

def normalize(nick: str) -> str:
    return mention(nick, ping=False).lower()

def similar(nick_a: str, nick_b: str) -> bool:
    return normalize(nick_a) == normalize(nick_b)

# Other formatting

def plural(
        number: int,
        if_plural: str = "s",
        if_singular: str = ""
        ) -> str:
    if number in [1, -1]:
        return if_singular
    else:
        return if_plural

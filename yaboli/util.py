import re

__all__ = ["mention", "atmention", "normalize", "similar"]

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

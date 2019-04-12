import datetime
import re

__all__ = ["mention", "atmention", "normalize", "similar", "plural",
        "format_time", "format_delta"]

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

def format_time(time: datetime.datetime) -> str:
    return time.strftime("%F %T")

def format_delta(delta: datetime.timedelta) -> str:
    seconds = int(delta.total_seconds())
    negative = seconds < 0
    seconds = abs(seconds)

    days = seconds // (60 * 60 * 24)
    seconds -= days * (60 * 60 * 24)

    hours = seconds // (60 * 60)
    seconds -= hours * (60 * 60)

    minutes = seconds // 60
    seconds -= minutes * 60

    text: str

    if days > 0:
        text = f"{days}d {hours}h {minutes}m {seconds}s"
    elif hours > 0:
        text = f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        text = f"{minutes}m {seconds}s"
    else:
        text = f"{seconds}s"

    if negative:
        text = "- " + text

    return text

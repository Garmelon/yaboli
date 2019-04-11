import abc
import re
from typing import (Awaitable, Callable, Dict, List, NamedTuple, Optional,
                    Pattern, Tuple)

from .message import LiveMessage
from .room import Room
from .util import similar

# Different ways of parsing commands:
#
# - raw string
#
# - split into arguments by whitespace
# - parsed into positional, optional, flags
#
# - The above two with or without bash-style escaping
#
# All of the above can be done with any argstr, even with an empty one.

__all__ = ["FancyArgs", "ArgumentData", "SpecificArgumentData", "CommandData",
        "Command", "GeneralCommandFunction", "GeneralCommand",
        "SpecificCommandFunction", "SpecificCommand"]

class FancyArgs(NamedTuple):
    positional: List[str]
    optional: Dict[str, Optional[str]]
    flags: Dict[str, int]

class ArgumentData:
    def __init__(self, argstr: str) -> None:
        self._argstr = argstr

        self._basic: Optional[List[str]] = None
        self._basic_escaped: Optional[List[str]] = None

        self._fancy: Optional[FancyArgs] = None
        self._fancy_escaped: Optional[FancyArgs] = None

    def _split_escaped(self, text: str) -> List[str]:
        words: List[str] = []
        word: List[str] = []

        backslash = False
        quotes: Optional[str] = None

        for char in text:
            if backslash:
                backslash = False
                word.append(char)
            elif quotes is not None:
                if char == quotes:
                    quotes = None
                else:
                    word.append(char)
            elif char.isspace():
                if word:
                    words.append("".join(word))
                    word = []
            else:
                word.append(char)

        # ignoring any left-over backslashes or open quotes at the end

        if word:
            words.append("".join(word))

        return words

    def _split(self, text: str, escaped: bool) -> List[str]:
        if escaped:
            return self._split_escaped(text)
        else:
            return text.split()

    def _parse_fancy(self, args: List[str]) -> FancyArgs:
        raise NotImplementedError

    @property
    def argstr(self) -> str:
        return self._argstr

    def basic(self, escaped: bool = True) -> List[str]:
        if escaped:
            if self._basic_escaped is None:
                self._basic_escaped = self._split(self._argstr, escaped)
            return self._basic_escaped
        else:
            if self._basic is None:
                self._basic = self._split(self._argstr, escaped)
            return self._basic

    def fancy(self, escaped: bool = True) -> FancyArgs:
        if escaped:
            if self._fancy_escaped is None:
                basic = self._split(self._argstr, escaped)
                self._fancy_escaped = self._parse_fancy(basic)
            return self._fancy_escaped
        else:
            if self._fancy is None:
                basic = self._split(self._argstr, escaped)
                self._fancy = self._parse_fancy(basic)
            return self._fancy

    def has_args(self) -> bool:
        return bool(self.basic()) # The list of arguments is empty

class SpecificArgumentData(ArgumentData):
    def __init__(self, nick: str, argstr: str) -> None:
        super().__init__(argstr)

        self._nick = nick

    @property
    def nick(self) -> str:
        return self._nick

class CommandData:
    _NAME_RE = re.compile(r"^!(\S+)")
    _MENTION_RE = re.compile(r"^\s+@(\S+)")

    def __init__(self,
            name: str,
            general: ArgumentData,
            specific: Optional[SpecificArgumentData]
            ) -> None:
        self._name = name
        self._general = general
        self._specific = specific

    @property
    def name(self) -> str:
        return self._name

    @property
    def general(self) -> ArgumentData:
        return self._general

    @property
    def specific(self) -> Optional[SpecificArgumentData]:
        return self._specific

    @staticmethod
    def _take(pattern: Pattern, text: str) -> Optional[Tuple[str, str]]:
        """
        Returns the pattern's first group and the rest of the string that
        didn't get matched by the pattern.

        Anchoring the pattern to the beginning of the string is the
        responsibility of the pattern writer.
        """

        match = pattern.match(text)
        if not match:
            return None

        group = match.group(1)
        rest = text[match.end():]

        return group, rest

    @classmethod
    def from_string(cls, string: str) -> "Optional[CommandData]":
        # If it looks like it should work in the euphoria UI, it should work.
        # Since euphoria strips whitespace chars from the beginning and end of
        # messages, we do too.
        string = string.strip()

        name_part = cls._take(cls._NAME_RE, string)
        if name_part is None: return None
        name, name_rest = name_part

        general = ArgumentData(name_rest)

        specific: Optional[SpecificArgumentData]
        mention_part = cls._take(cls._MENTION_RE, name_rest)
        if mention_part is None:
            specific = None
        else:
            mention, rest = mention_part
            specific = SpecificArgumentData(mention, rest)

        return cls(name, general, specific)

class Command(abc.ABC):
    def __init__(self, name: str) -> None:
        self._name = name

    async def run(self,
            room: Room,
            message: LiveMessage,
            nicks: List[str],
            data: CommandData,
            ) -> None:
        if data.name == self._name:
            await self._run(room, message, nicks, data)

    @abc.abstractmethod
    async def _run(self,
            room: Room,
            message: LiveMessage,
            nicks: List[str],
            data: CommandData,
            ) -> None:
        pass

# General command

GeneralCommandFunction = Callable[[Room, LiveMessage, ArgumentData],
        Awaitable[None]]

class GeneralCommand(Command):
    def __init__(self,
            name: str,
            cmdfunc: GeneralCommandFunction,
            args: bool
            ) -> None:
        super().__init__(name)

        self._cmdfunc = cmdfunc
        self._args = args

    async def _run(self,
            room: Room,
            message: LiveMessage,
            nicks: List[str],
            data: CommandData,
            ) -> None:
        # Do we have arguments if we shouldn't?
        if not self._args and data.general.has_args():
            return

        await self._cmdfunc(room, message, data.general)

# Specific command

SpecificCommandFunction = Callable[[Room, LiveMessage, SpecificArgumentData],
        Awaitable[None]]

class SpecificCommand(Command):
    def __init__(self,
            name: str,
            cmdfunc: SpecificCommandFunction,
            args: bool
            ) -> None:
        super().__init__(name)

        self._cmdfunc = cmdfunc
        self._args = args

    async def _run(self,
            room: Room,
            message: LiveMessage,
            nicks: List[str],
            data: CommandData,
            ) -> None:
        # Is this a specific command?
        if data.specific is None:
            return

        # Are we being mentioned?
        for nick in nicks:
            if similar(nick, data.specific.nick):
                break
        else:
            return # Yay, a rare occurrence of this structure!

        # Do we have arguments if we shouldn't?
        if not self._args and data.specific.has_args():
            return

        await self._cmdfunc(room, message, data.specific)

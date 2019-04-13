import contextlib
import http.cookies as cookies
import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

__all__ = ["CookieJar"]

class CookieJar:
    """
    Keeps your cookies in a file.

    CookieJar doesn't attempt to discard old cookies, but that doesn't appear
    to be necessary for keeping euphoria session cookies.
    """

    def __init__(self, filename: Optional[str] = None) -> None:
        self._filename = filename
        self._cookies = cookies.SimpleCookie()

        if not self._filename:
            logger.warning("Could not load cookies, no filename given.")
            return

        with contextlib.suppress(FileNotFoundError):
            logger.info(f"Loading cookies from {self._filename!r}")
            with open(self._filename, "r") as f:
                for line in f:
                    self._cookies.load(line)

    def get_cookies(self) -> List[str]:
        return [morsel.OutputString(attrs=[])
                for morsel in self._cookies.values()]

    def get_cookies_as_headers(self) -> List[Tuple[str, str]]:
        """
        Return all stored cookies as tuples in a list. The first tuple entry is
        always "Cookie".
        """

        return [("Cookie", cookie) for cookie in self.get_cookies()]

    def add_cookie(self, cookie: str) -> None:
        """
        Parse cookie and add it to the jar.

        Example cookie: "a=bcd; Path=/; Expires=Wed, 24 Jul 2019 14:57:52 GMT;
        HttpOnly; Secure"
        """

        logger.debug(f"Adding cookie {cookie!r}")
        self._cookies.load(cookie)

    def save(self) -> None:
        """
        Saves all current cookies to the cookie jar file.
        """

        if not self._filename:
            logger.warning("Could not save cookies, no filename given.")
            return

        logger.info(f"Saving cookies to {self._filename!r}")

        with open(self._filename, "w") as f:
            for morsel in self._cookies.values():
                cookie_string = morsel.OutputString()
                f.write(f"{cookie_string}\n")

    def clear(self) -> None:
        """
        Removes all cookies from the cookie jar.
        """

        logger.debug("OMNOMNOM, cookies are all gone!")
        self._cookies = cookies.SimpleCookie()

import contextlib
import http.cookies as cookies
import logging


logger = logging.getLogger(__name__)
__all__ = ["CookieJar"]


class CookieJar:
	"""
	Keeps your cookies in a file.
	"""

	def __init__(self, filename):
		self._filename = filename
		self._cookies = cookies.SimpleCookie()

		with contextlib.suppress(FileNotFoundError):
			with open(self._filename, "r") as f:
				for line in f:
					self._cookies.load(line)

	def sniff(self):
		"""
		Returns a list of Cookie headers containing all current cookies.
		"""

		return [morsel.OutputString(attrs=[]) for morsel in self._cookies.values()]

	def bake(self, cookie_string):
		"""
		Parse cookie and add it to the jar.
		Does not automatically save to the cookie file.

		Example cookie: "a=bcd; Path=/; Expires=Wed, 24 Jul 2019 14:57:52 GMT; HttpOnly; Secure"
		"""

		logger.debug(f"Baking cookie: {cookie_string!r}")

		self._cookies.load(cookie_string)

	def save(self):
		"""
		Saves all current cookies to the cookie jar file.
		"""

		logger.debug(f"Saving cookies to {self._filename!r}")

		with open(self._filename, "w") as f:
			for morsel in self._cookies.values():
				cookie_string = morsel.OutputString()
				#f.write(f"{cookie_string}\n")
				f.write(cookie_string)
				f.write("\n")

	def monster(self):
		"""
		Removes all cookies from the cookie jar.
		Does not automatically save to the cookie file.
		"""

		logger.debug("OMNOMNOM, cookies are all gone!")

		self._cookies = cookies.SimpleCookie()

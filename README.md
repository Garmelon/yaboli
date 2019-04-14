# Yaboli

Yaboli (**Y**et **A**nother **Bo**t **Li**brary) is a Python library for
creating bots for [euphoria.io](https://euphoria.io).

- [Documentation](docs/index.md)
- [Changelog](CHANGELOG.md)

## Installation

Ensure that you have at least Python 3.7 installed.

To install yaboli or update your installation to the latest version, run:
```
$ pip install git+https://github.com/Garmelon/yaboli@v1.1.1
```

The use of [venv](https://docs.python.org/3/library/venv.html) is recommended.

## Example echo bot

A simple echo bot that conforms to the
[botrulez](https://github.com/jedevc/botrulez) can be written like so:

```python
class EchoBot(yaboli.Bot):
    HELP_GENERAL = "/me echoes back what you said"
    HELP_SPECIFIC = [
            "This bot only has one command:",
            "!echo <text> – reply with exactly <text>",
    ]

    def __init__(self, config_file):
        super().__init__(config_file)
        self.register_botrulez(kill=True)
        self.register_general("echo", self.cmd_echo)

    async def cmd_echo(self, room, message, args):
        await message.reply(args.raw)
```

The bot's nick, cookie file and default rooms are specified in a config file.

The help command from the botrulez uses the `HELP_GENERAL` and `HELP_SPECIFIC`
fields.

In the `__init__` function, the bot's commands are registered. The required
botrulez commands (!ping, !help, !uptime) are enabled by default. Other
commands like !kill need to be enabled explicitly.

In the `cmd_echo` function, the echo command is implemented. In this case, the
bot replies to the message containing the command with the raw argument string,
i. e. the text between the end of the "!echo" and the end of the whole message.

## TODOs

- [ ] document yaboli (markdown files in a "docs" folder?)
- [ ] document new classes (docstrings, maybe comments)
- [ ] write examples
- [ ] make yaboli package play nice with mypy
- [x] implement !uptime for proper botrulez conformity
- [x] implement !kill
- [x] untruncate LiveMessage-s
- [x] config file support for bots, used by default
- [x] make it easier to enable log messages
- [x] make it easier to run bots
- [x] package in a distutils-compatible way (users should be able to install
  yaboli using `pip install git+https://github.com/Garmelon/yaboli`)
- [x] implement !restart
- [x] write project readme
- [x] cookie support
- [x] fancy argument parsing

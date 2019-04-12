# Yaboli

Yaboli (**Y**et **A**nother **Bo**t **Li**brary) is a Python library for
creating bots for [euphoria.io](https://euphoria.io).

Soon, markdown files containing documentation and troubleshooting info will be
available.

## Example echo bot

A simple echo bot that conforms to the
[botrulez](https://github.com/jedevc/botrulez) can be written like so:

```python
class EchoBot(yaboli.Bot):
    DEFAULT_NICK = "EchoBot"
    HELP_GENERAL = "/me echoes back what you said"
    HELP_SPECIFIC = [
            "This bot only has one command:",
            "!echo <text> – reply with exactly <text>",
    ]

    def __init__(self):
        super().__init__()
        self.register_botrulez()
        self.register_general("echo", self.cmd_echo)

    async def started(self):
        await self.join("test")

    async def cmd_echo(self, room, message, args):
        await message.reply(args.raw)
```

When joining a room, the bot sets its nick to the value in `DEFAULT_NICK`.

The help command from the botrulez uses the `HELP_GENERAL` and `HELP_SPECIFIC`
fields.

In the `__init__` function, the bot's commands are registered.

The `started` function is called when the bot has been started and is ready to
connect to rooms and do other bot stuff. It can be used to load config files or
directly connect to rooms.

In the `cmd_echo` function, the echo command is implemented. In this case, the
bot replies to the message containing the command with the raw argument string,
i. e. the text between the end of the "!echo" and the end of the whole message.

## TODOs

- [ ] implement !restart and add an easier way to run bots
- [ ] untruncate LiveMessage-s
- [ ] config file support for bots, used by default
- [ ] package in a distutils-compatible way (users should be able to install
  yaboli using `pip install git+https://github.com/Garmelon/yaboli`)
- [ ] document yaboli (markdown files in a "docs" folder?)
- [ ] make it easier to enable log messages
- [ ] cookie support
- [ ] fancy argument parsing
- [ ] document new classes (docstrings, maybe comments)
- [ ] write project readme
- [ ] write examples
- [x] implement !uptime for proper botrulez conformity
- [x] implement !kill

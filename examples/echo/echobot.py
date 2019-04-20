import yaboli


class EchoBot(yaboli.Bot):
    HELP_GENERAL = "/me echoes back what you said"
    HELP_SPECIFIC = [
            "This bot only has one command:",
            "!echo <text> – reply with exactly <text>",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.register_botrulez(kill=True)
        self.register_general("echo", self.cmd_echo)

    async def cmd_echo(self, room, message, args):
        text = args.raw.strip() # ignoring leading and trailing whitespace
        await message.reply(text)


if __name__ == "__main__":
    yaboli.enable_logging()
    yaboli.run(EchoBot)

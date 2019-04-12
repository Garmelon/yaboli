import asyncio

import yaboli


class EchoBot(yaboli.Bot):
    HELP_GENERAL = "/me echoes back what you said"
    HELP_SPECIFIC = [
            "This bot only has one command:",
            "!echo <text> – reply with exactly <text>",
    ]

    def __init__(self, config_file):
        super().__init__(config_file)
        self.register_botrulez()
        self.register_general("echo", self.cmd_echo)

    async def cmd_echo(self, room, message, args):
        await message.reply(args.raw)

async def main():
    bot = EchoBot("bot.conf")
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())

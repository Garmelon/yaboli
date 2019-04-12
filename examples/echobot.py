import asyncio

import yaboli

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

async def main():
    bot = EchoBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())

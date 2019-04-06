import yyb

class MyClient(yyb.Client):
    async def on_join(self, room):
        await room.say("Hello!")

    async def on_message(self, message):
        if message.content == "reply to me"):
            reply = await message.reply("reply")
            await reply.reply("reply to the reply")
            await message.room.say("stuff going on")

        elif message.content == "hey, join &test!":
            # returns room in phase 3, or throws JoinException
            room = await self.join("test")
            if room:
                room.say("hey, I joined!")
            else:
                message.reply("didn't work :(")

    async def before_part(self, room):
        await room.say("Goodbye!")

# Something like this, I guess. It's still missing password fields though.
c = MyClient("my:bot:")
c.run("test", "bots")

import json
import DatabaseTools.tool as tool

from nextcord.ext import commands


file_handle = open("config.JSON", "r")
config = json.loads(file_handle.read())
file_handle.close()


class Gavin(commands.Bot):
    connection, cursor = tool.connect()
    bot_name = "Gavin"
    if tool.create_tables(connection, cursor):
        print("Table checks okay.")

    def __init__(self, **kwargs):
        super(Gavin, self).__init__(**kwargs)

    async def on_ready(self):
        print(f'{self.user} has connected to discord!')

    @classmethod
    def prefixes(cls, client: None, message):
        guildID = message.guild.id
        prefix = tool.sql_retrieve_setting(guildID, "commandPrefix", cls.cursor)
        if prefix is None:
            return "!"
        else:
            return prefix


if __name__ == "__main__":
    bot = Gavin(command_prefix=Gavin.prefixes, max_messages=20_000)
    bot.load_extension('cogs.admincog')
    bot.load_extension('cogs.gavincog')
    print("Trying to login...")
    bot.run(TOKEN)

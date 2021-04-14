from os import getenv
from discord.ext import commands
from dotenv import load_dotenv
import DatabaseTools.tool as tool

load_dotenv()
TOKEN = getenv('DISCORD_TOKEN')


class Gavin(commands.Bot):
    connection, cursor = tool.connect()
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
    bot.load_extension('cogs.gavincog')
    bot.load_extension('cogs.admincog')
    print("Trying to login...")
    bot.run(TOKEN)

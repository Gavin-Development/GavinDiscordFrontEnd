from os import getenv
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = getenv('DISCORD_TOKEN')


class CustomClient(commands.Bot):
    def __init__(self, **kwargs):
        super(CustomClient, self).__init__(**kwargs)

    async def on_ready(self):
        print(f'{self.user} has connected to discord!')


if __name__ == "__main__":
    client = CustomClient(command_prefix="!")
    client.load_extension('cogs.gavincog')
    print("Trying to login...")
    client.run(TOKEN)

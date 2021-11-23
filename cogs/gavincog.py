import json

import requests
import re
import nextcord
import nextcord.utils
import datetime as dt
import DatabaseTools.tool as tool
from nextcord.ext import commands
from random import choice
from os import getenv
from dotenv import load_dotenv

load_dotenv()
DEFAULT_MODEL = getenv('DEFAULT_MODEL')
MODEL_PATHS = getenv('MODEL_PATHS')


# 😂

class Gavin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.archive_id = 785539080062631967
        self.phrases = ["My brain is in confinement until further notice",
                        "My brain is currently unavailable, please leave a message so I can ignore it, kthxbye"]
        # Inherit the connection from the Client defined in main.py
        self.connection, self.c = self.bot.connection, self.bot.cursor
        self.ids = ["<!810597892514381856>", "<810597892514381856>", "<!753611486999478322>", "<753611486999478322>"]
        self.loading = False
        self.chatbot_server = f"http://{self.bot.config['ServerHost']}:{self.bot.config['ServerPort']}"
        self.ModelName = self.get_model_name()
        self.bot_hparams = self.get_hparams()

    def get_hparams(self):
        response = requests.get(f"{self.chatbot_server}/chat_bot/hparams")
        data = response.json()
        return data

    def get_model_name(self):
        response = requests.get(f"{self.chatbot_server}/chat_bot/model_name")
        data = response.json()
        return data["ModelName"]

    @commands.Cog.listener()
    async def on_message(self, user_message: nextcord.Message):
        if not self.loading:
            await self.bot.change_presence(activity=nextcord.Game(name=f"Currently Using Model: {self.ModelName}"))
            if user_message.author != self.bot.user:
                pattern = re.compile(r"[^a-zA-Z?.!,'\"<>0-9 :]+")
                message = re.sub(pattern, "", user_message.content)
                words = message.split(' ')
                if words[0] in self.ids:
                    formatted_message = [words[1:]]
                    formatted_message = formatted_message[0]
                    message_for_bot = " ".join(formatted_message)
                    await self.chat(user_message, message_for_bot)
        else:
            if user_message.author != self.bot.user:
                channel_id = int(user_message.channel.id)
                channel = nextcord.utils.get(user_message.guild.text_channels, id=channel_id)
                await channel.send(choice(self.phrases))

    async def chat(self, message: nextcord.Message, content: str):
        channel_id = int(message.channel.id)
        channel = nextcord.utils.get(message.guild.text_channels, id=channel_id)
        async with channel.typing():
            web_response = requests.post(self.chatbot_server + "/chat_bot", data=json.dumps({'data': content}),
                                         headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
            if web_response.status_code == requests.codes.OK:
                data = web_response.json()
                response = data["message"]
                await tool.sql_insert_into_chat_logs(message.guild.id, str(message.channel.id), self.ModelName,
                                                     str(message.author),
                                                     message.content, response,
                                                     date=int(dt.datetime.utcnow().timestamp()),
                                                     connection=self.connection,
                                                     cursor=self.c)

                msg = f"> {content} \n{message.author.mention} {response}"
                print(f"""Date: {dt.datetime.now().strftime('%d/%m/%Y %H-%M-%S.%f')[:-2]}
Author: {message.author}
Where: {message.guild}:{message.channel}
Input: {content}
Output: {response}\n\n""")
                if response is None or response == "":
                    await channel.send("👎")
                    return
                else:
                    await channel.send(msg)
            else:
                print(f"Error: {web_response.status_code} {web_response.reason}")
                await channel.send("👎")

    @commands.command(name="hparams", aliases=['params', 'hp'])
    async def hparams(self, ctx: commands.Context):
        """Display the hparams of the mode. Aliases: params and hp"""
        fields = ["Num Layers", "Units", "D_Model", "Num Heads", "Dropout",
                  "Max Seq Len", "Tokenizer", "Model Name", "Mixed Precision",
                  "Epochs", "Save Freq", "Batch Size"]
        embed = nextcord.Embed(title=f"Hparams for {self.ModelName}", type="rich",
                               description="Displays the Hyper Parameters used for the bot")
        for i, value in enumerate(self.bot_hparams.values()):
            embed.add_field(name=f"{fields[i]}", value=f"{value}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="image", aliases=['img', 'im'])
    async def send_image(self, ctx: commands.Context):
        """Send the image of what the models Layers look like. Alias: img and im
        """
        """
        try: 
            with open(f"{MODEL_PATHS}{self.ModelName}/images/{self.ModelName}_Image.png", "rb") as f:
                picture = nextcord.File(f)
        except Exception as e:
            await ctx.send(f"Error on image send: {e}")
        else:
            await ctx.send(file=picture)        
        """  # TODO: Fix this
        await ctx.send("This command is currently under development.")
        return

    @commands.command(name="invite", aliases=['inv'])
    async def send_invite(self, ctx: commands.Context):
        """Send the bots invite link"""
        await ctx.send(
            f"You can add me here!\nhttps://discord.com/api/oauth2/authorize?client_id=753611486999478322&permissions=378944&scope=bot")

    @commands.command(name="history", aliases=['past', 'previous_messages'])
    async def send_history(self, ctx: commands.Context):
        """Send the past 10 messages for the guild."""
        # noinspection PyBroadException
        try:
            results = tool.sql_retrieve_last_10_messages(ctx.guild.id, self.connection, self.c)
            embed = nextcord.Embed(title=f"Message History for {ctx.guild.name}", type="rich",
                                   description="Shows the last 10 messages and responses from Gavin. For this guild")
            for result in results:
                embed.add_field(name=f"Model: {result[2]}\nPrompt: {' '.join(result[4].split(' ')[1:])}",
                                value=f"Author: {result[3]}\nReply: {result[5]}")
                print(result)
            await ctx.send(f"{ctx.message.author.mention}", embed=embed)
        except Exception as e:
            await ctx.send("👎")
            raise e


def setup(bot):
    bot.add_cog(Gavin(bot))

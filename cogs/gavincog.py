import re
import discord
import discord.utils
import datetime as dt
import concurrent.futures
import DatabaseTools.tool as tool
from discord.ext import commands
from random import choice
from backend import load_model, predict
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
        self.loading = True
        self.START_TOKEN, self.END_TOKEN, self.tokenizer, self.MAX_LENGTH, self.model, self.ModelName, self.hparams = load_model(
            f"{MODEL_PATHS}{DEFAULT_MODEL}")
        self.swear_words = ['cock', 'tf', 'reggin', 'bellend', 'twat',
                            'bollocks', 'wtf', 'slag', 'fucker', 'rapist',
                            'shit', 'bitch', 'minger', 'nigger', 'fking',
                            'wanker', 'hentai', 'ffs', 'porn', 'tits',
                            'fucking', 'knob', 'minge', 'clunge', 'whore',
                            'bloodclat', 'fuck', 'cunt', 'crap', 'pissed',
                            'prick', 'nickger', 'cocks', 'pussy', "fucking",
                            "bullshit", "slut", "fuckin'", "slut", "dick"]

        self.loading = False

    @commands.Cog.listener()
    async def on_message(self, user_message: discord.Message):
        if not self.loading:
            await self.bot.change_presence(activity=discord.Game(name=f"Loaded Model {self.ModelName}"))
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
                channel = discord.utils.get(user_message.guild.text_channels, id=channel_id)
                channel.send(choice(self.phrases))

    async def chat(self, message: discord.Message, content: str):
        channel_id = int(message.channel.id)
        channel = discord.utils.get(message.guild.text_channels, id=channel_id)
        async with channel.typing():
            response = await predict(content, self.tokenizer, self.swear_words, self.START_TOKEN, self.END_TOKEN,
                                     self.MAX_LENGTH, self.model)
            await tool.sql_insert_into_chat_logs(message.guild.id, str(message.channel.id), self.ModelName,
                                                 message.author,
                                                 message.content, response,
                                                 date=int(dt.datetime.utcnow().timestamp()), connection=self.connection,
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
                sent = await channel.send(msg)
                # await sent.add_reaction(emoji="😂")n
        return

    @commands.command(name="hparams", aliases=['params', 'hp'])
    async def hparams(self, ctx: commands.Context):
        """Display the hparams of the mode. Aliases: params and hp"""
        fields = ["Samples", "Max Length Of Words", "Batch Size", "Buffer Size", "Layers",
                  "d_model", "Heads", "Units", "Dropout", "Vocab Size", "Target Vocab Size"]
        embed = discord.Embed(title=f"Hparams for {self.ModelName}", type="rich",
                              description="Displays the Hyper Parameters used for the bot")
        for i, value in enumerate(self.hparams):
            embed.add_field(name=f"{fields[i]}", value=f"{value}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="reload", aliases=['r'])
    async def reload_model(self, ctx: commands.Context, model_name):
        """Reloads the model. !reload <model name>. Alias: r"""
        if ctx.message.author.id == 348519271460110338:
            self.loading = True
            await self.bot.change_presence(activity=discord.Game(name=f"Loading new model {model_name}"))
            with concurrent.futures.ThreadPoolExecutor(1) as executor:
                future = executor.submit(load_model, MODEL_PATHS + model_name)
                self.START_TOKEN, self.END_TOKEN, self.tokenizer, self.MAX_LENGTH, self.model, self.ModelName, self.hparams = future.result()
            self.loading = False
            await self.bot.change_presence(activity=discord.Game(name=f"Loaded into {model_name}"))

    @commands.command(name="image", aliases=['img', 'im'])
    async def send_image(self, ctx: commands.Context):
        """Send the image of what the models Layers look like. Alias: img and im"""
        try:
            with open(f"{MODEL_PATHS}{self.ModelName}/images/{self.ModelName}_Image.png", "rb") as f:
                picture = discord.File(f)
        except Exception as e:
            await ctx.send(f"Error on image send: {e}")
        else:
            await ctx.send(file=picture)

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
            embed = discord.Embed(title=f"Message History for {ctx.guild.name}", type="rich",
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

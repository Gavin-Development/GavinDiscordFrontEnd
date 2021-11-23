import nextcord

import DatabaseTools.tool as tool
from discord.ext import commands
from discord import Embed
from main import Gavin

import discord.utils
import re


class Admin(commands.Cog):
    error_emoji = "👎"
    success_emoji = "👍"

    def __init__(self, bot: Gavin, verbose=True):
        """Admin Cog. Core functions for members with Administrator Permissions (Or Bot Owner Scot_Survivor)"""
        self.bot = bot
        self._last_member = None
        self.verbose = verbose
        self.function_names = ["Reload Module", "Modules List"]
        self.functions = [self.reload_module, self.modules]
        self.connection, self.c = self.bot.connection, self.bot.cursor
        self.bot_name = self.bot.bot_name

    @commands.command(name="activity")
    async def activity(self, ctx: commands.Context):
        if ctx.message.author.id == 348519271460110338:
            await self.bot.change_presence(activity=nextcord.Game(name=ctx.message.content))

    @commands.command(name="stop")
    async def stop(self, ctx: commands.Context):
        if ctx.message.author.id == 348519271460110338:
            await ctx.send("Stopping the bot.\nReason: Owner Invoked Command.")
            quit()

    @commands.command(name="reload_module", invoke_without_command=True)
    async def reload_module(self, ctx: commands.Context, *, module):
        """Syntax: !reload cogs.<module name>
        Reloads a module.
        """
        if ctx.message.author.guild_permissions.administrator:
            try:
                self.bot.reload_extension(module)
            except commands.ExtensionError as e:
                await ctx.send(f"{e.__class__.__name__}: {e}")
            else:
                await ctx.send("👍")
        else:
            return

    @commands.command(name="modules", invoke_without_command=True)
    async def modules(self, ctx: commands.Context):
        """Syntax: !modules <>
        Part of admin cog
        :return a list of numbers"""
        if ctx.message.author.guild_permissions.administrator:
            embed = Embed(title="Gavin: Here are the modules")
            for m_name, c_object in self.bot.cogs.items():
                embed.add_field(name=f"Module: {m_name}", value=f"Reload: cogs.{m_name.lower()}cog", inline=False)
            await ctx.channel.send(embed=embed)

    @commands.command(name="disable")
    async def disable(self, ctx, *, args):
        """"Syntax: !disable #channel module command(without the !)
        Part of admin cog"""
        if ctx.message.author.guild_permissions.administrator:
            args = args.split(" ")
            channel = args[0]
            module = args[1]
            command = args[2]
            channel = int(re.sub(r"[<>#]", "", channel))
            guild = ctx.message.guild.id
            check = tool.sql_insert_command_disabled_commands(guild, channel, module, command, self.c, self.connection)
            if type(check) == bool:
                await ctx.send("👍")
            else:
                await ctx.send(check)

    # noinspection DuplicatedCode
    @commands.command(name="disabled")
    async def disabled(self, ctx):
        """Display Disabled Commands"""
        results = tool.returnDisabled(ctx.message.guild.id, self.c)
        modules = {}
        for m_name, c_object in self.bot.cogs.items():
            modules[f"cogs.{m_name.lower()}cog"] = {}
        for collection in results:
            module = collection[0]
            command = collection[1]
            channelID = "<#" + str(collection[2]) + ">"
            try:
                modules[module][channelID] = command
            except KeyError as e:
                print(f"Error: {e}")
        embeds = []
        embedsTitle = []
        for i, collection in enumerate(results):
            moduleName = collection[0]
            title = f"Disabled for: {moduleName}"
            if i == 0:
                embed = Embed(title=title)
                embedsTitle.append(title)
                embeds.append(embed)
                if modules[moduleName]:
                    for key, value in modules[moduleName].items():
                        embed.add_field(name=f"Command: {str(value)}", value=f"Channel: !{str(key)}")
            else:
                if title in embedsTitle:
                    e = embedsTitle.index(title)
                    c_embed = embeds[e]
                    if modules[moduleName]:
                        for key, value in modules[moduleName].items():
                            c_embed.add_field(name=f"Command: {str(value)}", value=f"Channel: !{str(key)}")
                else:
                    embed = Embed(title=title)
                    embedsTitle.append(title)
                    embeds.append(embed)
                    if modules[moduleName]:
                        for key, value in modules[moduleName].items():
                            embed.add_field(name=f"Command: {str(value)}", value=f"Channel: !{str(key)}")
        for embed in embeds:
            await ctx.send(embed=embed)

    @commands.command(name="prefix", aliases=['p'])
    async def prefix_update(self, ctx: commands.Context, *, prefix):
        """Update the prefix"""
        if ctx.message.author.guild_permissions.administrator:
            try:
                tool.sql_update_setting(int(ctx.message.guild.id), "commandPrefix", prefix, self.c, self.connection)
                await ctx.send(self.success_emoji)
            except Exception as e:
                await ctx.send(self.error_emoji)
                if self.verbose:
                    raise e

    @commands.command(name="shout")
    async def shout(self, ctx: commands.Context, *, msg):
        if ctx.message.author.id == 348519271460110338:
            pass

    def returnHelp(self):
        return f"{self.__doc__}"

    def returnProperties(self):
        return self.functions, self.function_names

    def checkRun(self, channel, module, command, guild):
        return tool.sql_check_disabled_commands(guild, channel, command, module, self.c)


def setup(bot):
    bot.add_cog(Admin(bot))

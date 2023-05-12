import discord
from discord.commands import Option, slash_command
from discord.ext import commands

import bot as Bot

class About(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@slash_command(description="このBotについての情報を表示します。")
	async def about(self, ctx: discord.ApplicationContext):
		# Pingを取得
		raw_ping = Bot.Client.latency
		ping = round(raw_ping * 1000)

		# 埋め込みメッセージを作成
		embed = discord.Embed(color=discord.Colour.from_rgb(217, 47, 152))
		embed.set_author(name=Bot.Name, icon_url=Bot.Client.user.display_avatar.url)
		embed.add_field(name=f"Version", value=f"`{Bot.Version}`")
		embed.add_field(name=f"Pycord", value=f"`{discord.__version__}`")
		embed.add_field(name=f"Ping", value=f"**`{ping}`** ms")
		embed.set_footer(text=f"Developed by Milkeyyy")

		# 作成した埋め込みメッセージで返信
		await ctx.respond(embed=embed)

def setup(bot):
    bot.add_cog(About(bot))

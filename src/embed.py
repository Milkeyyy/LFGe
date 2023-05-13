import discord

def success():
	embed = discord.Embed(
		title=":white_check_mark: ",
		colour=discord.Colour.from_rgb(140, 176, 91)
	)
	return embed

def warning():
	embed = discord.Embed(
		title=":warning: ",
		colour=discord.Colour.from_rgb(228, 146, 16)
	)
	return embed

def error():
	embed = discord.Embed(
		title=":no_entry_sign: ",
		colour=discord.Colour.from_rgb(247, 206, 80)
	)
	return embed

def internal_error():
	embed = discord.Embed(
		title=":closed_book: 内部エラー",
		description = "内部エラーが発生しました。もう一度お試しください。\n(この問題が解決しない場合は、開発者へ報告してください。)",
		colour=discord.Colour.from_rgb(205, 61, 66)
	)
	return embed

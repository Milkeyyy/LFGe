import logging
import os
import traceback
from logging import info

import discord
from discord.ext import commands

import bot as Bot
import data as Data
import lfg_worker as LFGWorker


logging.basicConfig(level=logging.INFO)
#logging.basicConfig(level=logging.DEBUG)


# スプラッシュテキストを表示
print("")
print("---------------------------------------")
print(f" {Bot.Name} Bot - Version {Bot.Version}")
print(f" using Pycord {discord.__version__}")
print(f" Developed by Milkeyyy")
print("---------------------------------------")
print("")

# Bot起動時のイベント
@Bot.Client.event
async def on_ready():
	print("")
	info(f"{Bot.Client.user} へログインしました！ (ID: {Bot.Client.user.id})")

	#プレゼンスを設定
	await Bot.Client.change_presence(activity=discord.Game(
		name=f"/help | Version {Bot.Version}"))

	# ユーザーデータを作成
	Data.create_user_data()

	# ギルドデータを確認&読み込み
	Data.check_guild_data()

	LFGWorker.updatelfgstatus.start()


# Botへログイン
try:
	Bot.Client.load_extension("commands.about")
	Bot.Client.load_extension("commands.lfg")
	Bot.Client.run(os.getenv("BOT_TOKEN"))
except Exception as e:
	logging.error(traceback.format_exc())

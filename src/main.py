import logging
import traceback
from logging import info
from os import environ, getcwd, path

import discord
from discord.ext import commands
from dotenv import load_dotenv

import bot as Bot
import commands.lfg as LFGModule
import commands.lfgui as LFGUIModule
import data as Data
import lfg_worker as LFGWorker

logging.basicConfig(level=logging.INFO)
logging.basicConfig(level=logging.ERROR)


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

	# 永続ビューの登録 (LFGUI)
	Bot.Client.add_view(LFGUIModule.MainView())

	LFGWorker.updatelfgstatus.start()


# Botへログイン
try:
	# .envを読み込む
	env_path = path.join(getcwd(), ".env")
	info("環境変数を読み込み: " + env_path)
	load_dotenv(env_path)

	# データベースを取得
	info("データベースを取得")
	Data.deta = Data.Deta(environ["DETA_PROJECT_KEY"])

	# コマンドたちの読み込み
	Bot.Client.load_extension("commands.about")
	Bot.Client.load_extension("commands.lfg")
	Bot.Client.load_extension("commands.lfgui")

	Bot.Client.run(environ["BOT_TOKEN"])
except Exception as e:
	logging.error(traceback.format_exc())

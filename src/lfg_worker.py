import datetime
import logging
import traceback

import discord
from discord.ext import tasks
from box import Box

import bot as Bot
import data as Data

# 1分毎に募集状況を更新する
lfg_loop_isrunning = False

@tasks.loop(seconds=10.0)
async def updatelfgstatus():
	global lfg_loop_isrunning

	lfg_loop_isrunning = True

	logging.info("LFGの更新開始")
	for g in Bot.Client.guilds:
		logging.info(f"- ギルド: {g.name} ({g.id})")
		for user_id in Data.userdata[g.id].keys():
			#logging.info(type(k))
			#logging.info(type(v))
			# ユーザーデータを取得 存在しない場合はチェックをスキップ
			ud = Data.userdata[g.id][user_id]
			if ud == None: continue
			# LFGが行われていないユーザーはスキップ
			if ud.LFG.Status != True: continue

			logging.info(f"-- 確認 - ユーザーID: {user_id} / " + str(ud.LFG.Status))

			to = ud.LFG.Timeout
			dt = datetime.datetime.now() - to
			logging.info(f"--- 時間差分: {dt.total_seconds()} sec")
			if dt.total_seconds() >= 0.0:
				# メッセージIDからメッセージを取得
				try:
					msg = Bot.Client.get_message(ud.LFG.Message_ID)
				except Exception as e:
					logging.error("--- メッセージの取得に失敗")
					logging.error(traceback.format_exc())
					continue
				# 募集を終了
				logging.info("-- メンバー募集終了 (時間切れ) - ID: " + str(ud.LFG.ID))
				await EndLFG(1, msg.guild.id, user_id)
			#else:
				#invd["timeleft"] == invd["timeleft"] - 1
	logging.info("LFGの更新終了")

@updatelfgstatus.before_loop
async def before_updatelfgstatus():
	logging.info("LFGの定期更新開始")

@updatelfgstatus.after_loop
async def after_updatelfgstatus():
	global lfg_loop_isrunning
	lfg_loop_isrunning = False
	logging.info("LFGの定期更新終了")


async def StartLFG(guild, author, msgid, game, nom, timeout):
	ud = Data.userdata[guild][author]
	ud.LFG.update(
		Status = True,
		ID = author,
		Message_ID = msgid,
		Game = game,
		Max_Number_Of_Member = nom,
		Timeout = datetime.datetime.now() + datetime.timedelta(minutes=timeout)
	)

	logging.info(f"LFG開始 - ID: {author}")
	logging.info(f"- メッセージID: " + str(ud.LFG.Message_ID))
	logging.info(f"- ゲームタイトル: " + str(ud.LFG.Game))
	logging.info(f"- 募集人数: " + str(ud.LFG.Max_Number_Of_Member))
	logging.info(f"- 募集締め切り時刻: " + str(ud.LFG.Timeout))

	# 募集者本人をメンバーに加える
	ud.LFG.Member.append(author)

async def EndLFG(endtype, guild, author):
	ud = Data.userdata[guild][author]

	message_id = ud.LFG.Message_ID

	# メッセージIDからメッセージを取得
	msg = Bot.Client.get_message(message_id)
	if msg == None:
		logging.warning(f"募集メッセージが見つかりません - ID: {message_id}")
		# ユーザーデータのLFG項目をリセットする
		ud.LFG = Box(Data.default_userdata_item["LFG"])
		# ユーザーデータの募集状態を無効に変える
		ud.LFG.Status = False
		return

	# メッセージから埋め込みメッセージを取得
	msgembed = msg.embeds[0]

	# 既存の募集メッセージを埋め込みメッセージで編集する
	if endtype == 1: # 締め切り
		msgembed.color = discord.Colour.from_rgb(205, 61, 66)
		msgembed.description = ":no_entry_sign: この募集は締め切られました。"
	elif endtype == 2: # キャンセル
		msgembed.color = discord.Colour.from_rgb(228, 146, 16)
		msgembed.description = ":orange_square: この募集はキャンセルされました。"

	await msg.edit(embed=msgembed, view=None)

	# ユーザーデータのLFG項目をリセットする
	ud.LFG = Data.default_userdata_item["LFG"]
	# ユーザーデータの募集状態を無効に変える
	ud.LFG.Status = False

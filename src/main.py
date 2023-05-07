import datetime
import logging
import os
import traceback
from logging import info

import discord
from deta import Deta
from discord.commands import Option

import bot as Bot
import config as Config
import data as Data
import lfg_worker as LFGWorker
import util as Util

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


client = Bot.Client


# Bot起動時のイベント
@client.event
async def on_ready():
	print("")
	info(f"{client.user} へログインしました！ (ID: {client.user.id})")

	#プレゼンスを設定
	await client.change_presence(activity=discord.Game(
		name=f"/help | Version {Bot.Version}"))

	# ユーザーデータを作成
	Data.createUserData()

	# ギルドデータを確認&読み込み
	Data.checkGuildData()

	LFGWorker.updatelfgstatus.start()


# コマンド
@client.command(description="このBotの情報を表示します。")
async def about(ctx):
	embed = discord.Embed(color=discord.Colour.from_rgb(234, 197, 28))
	embed.set_author(name=Bot.Name, icon_url=client.user.display_avatar.url)
	raw_ping = client.latency
	ping = round(raw_ping * 1000)
	embed.add_field(name=f"Version", value=f"`{Bot.Version}`")
	embed.add_field(name=f"Pycord", value=f"`{discord.__version__}`")
	embed.add_field(name=f"Ping", value=f"**`{ping}`** ms")
	embed.set_footer(text=f"Developed by Milkeyyy")
	await ctx.respond(embed=embed)


class InviteView(discord.ui.View):

	@discord.ui.button(label="参加", emoji="✅", style=discord.ButtonStyle.green)
	async def button_callback(self, button, interaction):
		# 募集IDを取得
		try:
			lfgid = int(interaction.message.embeds[0].footer.text.lstrip("ID: "))
		except:
			self.clear_items()
			return
		ud = Data.userdata[interaction.guild.id][int(lfgid)]

		rmsg = interaction.message
		if type(rmsg) != discord.Message:
			return

		async def updateMemberList():
			try:
				original_embed = rmsg.embeds[0]
			except:
				return

			for field in original_embed.fields:
				if field.name.startswith(":busts_in_silhouette: 参加者") is True:
					field.name = f":busts_in_silhouette: 参加者 ({len(ud.LFG.Member)}/{ud.LFG.Max_Number_Of_Member + 1})"
					field.value = Util.convertToUserBulletPointsFromIDList(ud.LFG.Member)
			await rmsg.edit(rmsg.content, embed=original_embed, view=InviteView())

		async def sendJoinMessage():
			# 埋め込みメッセージを作成して返信
			embed = discord.Embed(color=discord.Colour.from_rgb(131, 177, 88))
			embed.set_author(name=f"{interaction.user} さんが参加しました", icon_url=interaction.user.display_avatar.url)
			embed.set_footer(text=f"ID: {lfgid}")
			await interaction.response.send_message(embed=embed)

		# 募集IDを取得
		try:
			lfgid = int(interaction.message.embeds[0].footer.text.lstrip("ID: "))
		except:
			self.clear_items()
			return
		# 募集者のIDを取得
		author_id = lfgid

		info(f"ボタン押下 - ユーザー: {interaction.user.name} ({interaction.user.id})")
		info("- メンバー: " + str(ud.LFG.Member))

		# ボタンを押したのが募集者本人の場合
		if author_id == interaction.user.id:
			embed = discord.Embed(
				color=discord.Colour.from_rgb(205, 61, 66),
				description=":no_entry_sign: 自分で自分の募集に参加することはできません...:cry:")
			msg = await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
		# それ以外の場合
		else:
			# 既に募集に参加している場合
			if interaction.user.id in ud.LFG.Member:
				embed = discord.Embed(
					color=discord.Colour.from_rgb(205, 61, 66),
					description=":no_entry_sign: あなたは既にこの募集に参加しています！")
				msg = await interaction.response.send_message(embed=embed, ephemeral=True, delete_after=5)
			# 募集に参加していない場合
			else:
				# 最大人数に達する場合
				if len(ud.LFG.Member) >= ud.LFG.Max_Number_Of_Member:
					# 募集データにユーザーIDを追加
					ud.LFG.Member.append(interaction.user.id)
					await updateMemberList()
					await sendJoinMessage()
					# 募集を締め切る
					await LFGWorker.EndLFG(1, rmsg.guild.id, lfgid)
					return
				else:
					# 募集データにユーザーIDを追加
					ud.LFG.Member.append(interaction.user.id)
					await updateMemberList()
					await sendJoinMessage()


@client.command(description="新しくメンバーの募集を開始します。")
async def lfg(
	ctx,
	game: Option(
		str,
		name="ゲーム",
		description="募集するゲームタイトル",
		choices=dict.keys(Data.gamelist)
	),
	nom: Option(
		int,
		name="募集人数",
		description="募集する人数 (自分を除く)",
		autocomplete=discord.utils.basic_autocomplete(list(range(1, 100)))
	),
	timeout: Option(
		float,
		required=False,
		min_value=1,
		max_value=600,
		default=15,
		name="制限時間",
		description="募集を締め切るまでの時間(分)を指定します。 (指定しない場合は15分になります。)",
		autocomplete=discord.utils.basic_autocomplete(list(range(1, 60)))
	)
):
	# 分→秒
	#timeout = timeout * 60

	ud = Data.userdata[ctx.guild.id][ctx.author.id]
	if ud["LFG"]["Status"] == True:
		embed = discord.Embed(color=discord.Colour.from_rgb(205, 61, 66))
		embed.add_field(name=f":no_entry_sign: 既に募集が開始されています！", value=f"再度募集を行うには、一度募集をキャンセルしてください！")
		embed.set_author(name=Bot.Name, icon_url=client.user.display_avatar.url)
		await ctx.respond(embed=embed, ephemeral=True)
	else:
		#ud["LFG"]["Status"] = True
		#ud["LFG"]["Game"] = game
		# ギルドデータを取得する
		gd = Data.guilddata.get(str(ctx.guild.id))
		# メンションするロールのIDを取得
		rid = gd["Game_List"][game]["Role_ID"]
		# メンションするロールをIDから取得 ロールが設定されていない場合は、メンションしない
		if rid == 0 or None:
			role = ""
		else:
			# ロールが設定されている場合は <@ID> になる
			role = ctx.guild.get_role(rid).mention

		# 募集IDを生成
		id = ctx.author.id

		# 募集用埋め込みメッセージを作成
		embed = discord.Embed(color=discord.Colour.from_rgb(131, 177, 88), title=":loudspeaker: メンバー募集")
		embed.add_field(name=f"🎮 ゲーム", value=f"{game}")
		embed.add_field(name="**@**", value=f"**`{nom}`**")
		embed.add_field(name=f":busts_in_silhouette: 参加者 (1/{nom + 1})", value=f"・{ctx.author.mention}")
		embed.set_footer(text=f"ID: {id}")
		embed.set_author(name=f"{ctx.author}", icon_url=ctx.author.display_avatar.url)
		# 募集メッセージを送信 (募集用テキストチャンネルが指定されていない場合は、コマンドが実行されたチャンネルへ送信する)
		if gd["LFG_Channel"] == 0:
			rch = client.get_channel(ctx.channel_id)
		else:
			rch = client.get_channel(gd["LFG_Channel"])

		rmsg = await rch.send(f"{role}", embed=embed, view=InviteView())

		# 募集開始通知用埋め込みメッセージを作成
		notification_embed = discord.Embed(
			color=discord.Colour.from_rgb(112, 171, 235),
			title="メンバーの募集を開始しました。",
			description=f"[募集メッセージを表示]({rmsg.jump_url})")
		notification_embed.add_field(name=f"🎮 ゲーム", value=f"{game}")
		notification_embed.add_field(name="**@**", value=f"**`{nom}`**")
		notification_embed.set_footer(text=f"ID: {id}")
		# 募集開始通知を募集者へ送信する (返信)
		await ctx.respond(embed=notification_embed, ephemeral=True)
		# メッセージのIDを取得
		msgid = rmsg.id
		# 募集データを作成
		await LFGWorker.StartLFG(ctx.guild.id, ctx.author.id, msgid, game, nom, timeout)

@client.command(description="現在行っているメンバーの募集を終了します。")
async def endlfg(ctx):
	ud = Data.userdata[ctx.guild.id][ctx.author.id]
	if ud.LFG.Status == False:
		embed = discord.Embed(
			color=discord.Colour.from_rgb(191, 71, 65),
			title="メンバーの募集が実行されていません。",
			description=f"メンバーの募集を行っていないため、終了することはできません。"
		)
	else:
		embed = discord.Embed(
			color=discord.Colour.from_rgb(191, 71, 65),
			title="メンバーの募集を終了しました。",
			description=f"[募集メッセージを表示](" + Bot.Client.get_message(ud.LFG.Message_ID).jump_url + ")"
		)
		embed.add_field(name=f"🎮 ゲーム", value=f"{ud.LFG.Game}")
		embed.add_field(name="**@**", value=f"**`{ud.LFG.Max_Number_Of_Member}`**")
		embed.set_footer(text=f"ID: {ud.LFG.ID}")

	# 募集終了処理を実行する
	await LFGWorker.EndLFG(1, ctx.guild.id, ctx.author.id)

	# 募集終了通知を送信する
	await ctx.respond(embed=embed, ephemeral=True)


# ログイン
try:
	client.run(os.getenv("BOT_TOKEN"))
except Exception as e:
	logging.error(traceback.format_exc())

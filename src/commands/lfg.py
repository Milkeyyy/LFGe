import datetime
import traceback
from logging import error, info, warning

import discord
from discord.commands import Option, SlashCommandGroup
from discord.ext import commands

import bot as Bot
import config as Config
import data as Data
import embed as EmbedTemplate
import lfg_worker as LFGWorker
import util as Util


class Config(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	# コマンドグループを定義する
	config = SlashCommandGroup("config", "Config Commands")

	# コマンドたち
	@config.command(description="メンバー募集メッセージを送信するテキストチャンネルを設定します。")
	async def lfgchannel(
		self,
		ctx: discord.ApplicationContext,
		channel: Option(
			discord.TextChannel,
			name="テキストチャンネル",
			description="メンバー募集メッセージを送信するテキストチャンネル"
		)
	):
		#await ctx.response.defer()

		try:
			# データベースのテキストチャンネルを更新
			Data.guilddata.update(
				{
					"LFG_Channel": str(channel.id)
				},
				str(ctx.guild.id)
			)
			# 埋め込みメッセージで返信
			embed = discord.Embed(
				title=":gear: コンフィグ",
				description=f"メンバー募集テキストチャンネルを {channel.mention} に設定しました。",
				color=discord.Colour.from_rgb(106, 170, 238)
			)
			await ctx.respond(embed=embed)
		except Exception as e:
			error("- データベース更新エラー")
			error(traceback.format_exc())
			embed = EmbedTemplate.error
			embed.title = embed.title + "エラーが発生しました"
			embed.description = "データベースの更新時にエラーが発生しました。もう一度お試しください。\n(解決しない場合、この問題を開発者へ報告してください。)"
			embed.add_field(name="エラー内容", value=f"```{str(e)}```")
			await ctx.response.send_message(embed=embed)

	@config.command(description="各ゲームのメンバー募集時にメンションするロールを設定します。")
	async def role(
		self,
		ctx: discord.ApplicationContext,
		game: Option(
			str,
			name="ゲーム",
			description="設定を変更する対象のゲームを指定します。",
			choices=dict.keys(Data.gamelist)
		),
		role: Option(
			discord.Role,
			name="ロール",
			description="対象のゲームで募集を行った際にメンションするロールを指定します。"
		)
	):
		#await ctx.response.defer()

		try:
			if role.mentionable == False:
				embed = EmbedTemplate.error
				embed.title = embed.title + "エラー"
				embed.description = f"指定されたロール `{role.name}` は、メンションが許可されていません！"
			else:
				# データベースのロールIDを更新
				Data.guilddata.update(
					{
						f"Game_List.{game}.Role_ID": str(role.id)
					},
					str(ctx.guild.id)
				)
				# 埋め込みメッセージ
				embed = discord.Embed(
					title=":gear: コンフィグ",
					description=f"`{game}` の対象ロールを `{role.name} ({role.id})` に設定しました。",
					color=discord.Colour.from_rgb(106, 170, 238)
				)
			await ctx.respond(embed=embed)
		except Exception as e:
			error("- エラー")
			error(traceback.format_exc())
			embed = EmbedTemplate.internal_error
			embed.add_field(name="エラー内容", value=f"```{str(e)}```")
			await ctx.response.send_message(embed=embed)

class LFG(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	# コマンドグループを定義する
	lfg = SlashCommandGroup("lfg", "LFG Commands")

	# 埋め込み

	async def cancel_embed(ud) -> discord.Embed:
		if ud.LFG.Status == False:
			embed = discord.Embed(
				title=":warning: メンバーの募集が実行されていません。",
				description=f"メンバーの募集を行っていないため、キャンセルすることはできません。",
				color=discord.Colour.from_rgb(247, 206, 80)
			)
		else:
			embed = discord.Embed(
					title=":yellow_square: メンバーの募集をキャンセルしました。",
					description=f"[募集メッセージを表示](" + Bot.Client.get_message(ud.LFG.Message_ID).jump_url + ")",
					color=discord.Colour.from_rgb(228, 146, 16)
				)
			embed.add_field(name=f"🎮 ゲーム", value=f"**{ud.LFG.Game}**")
			embed.add_field(name="*️⃣ 人数", value=f"**`{ud.LFG.Max_Number_Of_Member}`**人")
			embed.set_footer(text=f"ID: {ud.LFG.ID}")
		return embed

	async def end_embed(ud) -> discord.Embed:
		if ud.LFG.Status == False:
			embed = discord.Embed(
				title=":warning: メンバーの募集が実行されていません。",
				description=f"メンバーの募集を行っていないため、終了することはできません。",
				color=discord.Colour.from_rgb(247, 206, 80)
			)
		else:
			embed = discord.Embed(
				title=":red_square: メンバーの募集を終了しました。",
				description=f"[募集メッセージを表示](" + Bot.Client.get_message(ud.LFG.Message_ID).jump_url + ")",
				color=discord.Colour.from_rgb(205, 61, 66)
			)
			embed.add_field(name=f"🎮 ゲーム", value=f"**{ud.LFG.Game}**")
			embed.add_field(name="*️⃣  人数", value=f"**`{ud.LFG.Max_Number_Of_Member}`**人")
			embed.set_footer(text=f"ID: {ud.LFG.ID}")
		return embed

	# コマンドたち
	@lfg.command(description="新しくメンバーの募集を開始します。")
	async def start(
		self,
		ctx: discord.ApplicationContext,
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
		#await ctx.response.defer()

		try:
			# ユーザーデータを取得する
			ud = Data.userdata[ctx.guild.id][ctx.author.id]
			if ud.LFG.Status == True:
				embed = discord.Embed(
					title=":warning: 既に募集が開始されています！",
					description="再度募集を行うには、一度募集をキャンセルしてください！",
					color=discord.Colour.from_rgb(247, 206, 80)
				)
				await ctx.respond(embed=embed, ephemeral=True)
			else:
				# ギルドデータを取得する
				gd = Data.guilddata.get(str(ctx.guild.id))
				# メンションするロールのIDを取得
				rid = int(gd["Game_List"][game]["Role_ID"])
				# メンションするロールをIDから取得 ロールが設定されていない場合は、メンションしない
				if rid == 0 or None:
					role = ""
				else:
					# ロールが設定されている場合は <@ID> になる
					role = ctx.guild.get_role(rid)
					if role == None:
						role = ""
					else:
						role = role.mention

				# 募集IDを生成 (ユーザーID)
				id = ctx.author.id

				# 締め切り時間
				timestamp = int((datetime.datetime.now() + datetime.timedelta(minutes=timeout)).timestamp())

				# 募集用埋め込みメッセージを作成
				embed = discord.Embed(color=discord.Colour.from_rgb(131, 177, 88), title=":loudspeaker: メンバー募集")
				embed.add_field(name=f"🎮 ゲーム", value=f"**{game}**")
				embed.add_field(name=f"🕒 締め切り", value=f"**<t:{timestamp}:f>\n(<t:{timestamp}:R>)**")
				embed.add_field(name="\u200B", value="\u200B")
				embed.add_field(name=f":busts_in_silhouette: 参加者 (1/{nom + 1})", value=f"・{ctx.author.mention}")
				embed.add_field(name="*️⃣  人数", value=f"**{nom}**人")
				embed.set_footer(text=f"ID: {id}")
				embed.set_author(name=f"{ctx.author}", icon_url=ctx.author.display_avatar.url)

				# 募集メッセージを送信 (募集用テキストチャンネルが指定されていない場合は、コマンドが実行されたチャンネルへ送信する)
				rch = Bot.Client.get_channel(int(gd["LFG_Channel"]))
				if rch == None: rch = Bot.Client.get_channel(ctx.channel_id)
				rmsg = await rch.send(content=f"{role}", embed=embed, view=LFGView(timeout=None))

				# 募集開始通知用埋め込みメッセージを作成
				notification_embed = discord.Embed(
					title=":arrow_forward: メンバーの募集を開始しました。",
					description=f"[募集メッセージを表示]({rmsg.jump_url})",
					color=discord.Colour.from_rgb(79, 134, 194)
				)
				notification_embed.add_field(name=f"🎮 ゲーム", value=f"**{game}**")
				notification_embed.add_field(name=f"🕒 締め切り", value=f"**<t:{timestamp}:f>\n(<t:{timestamp}:R>)**")
				embed.add_field(name="\u200B", value="\u200B")
				notification_embed.add_field(name="*️⃣  人数", value=f"**{nom}**人")
				notification_embed.set_footer(text=f"ID: {id}")

				# 募集を開始する
				await LFGWorker.start_lfg(ctx.guild.id, ctx.author.id, rmsg.id, game, nom, timeout)

				# 募集開始通知を募集者へ送信する (返信)
				await ctx.respond(embed=notification_embed, view=ToiregaKitanaiOmisetteIyadayoneView(timeout=None), ephemeral=True)
		except Exception as e:
			error("- エラー")
			error(traceback.format_exc())
			embed = EmbedTemplate.internal_error
			embed.add_field(name="エラー内容", value=f"```{str(e)}```")
			await ctx.response.send_message(embed=embed, ephemeral=True)

	@lfg.command(description="現在行っているメンバーの募集を終了します。")
	async def end(self, ctx: discord.ApplicationContext):
		try:
			# ユーザーデータを取得する
			ud = Data.userdata[ctx.guild.id][ctx.author.id]
			# 埋め込みメッセージを作成
			embed = await self.end_embed(ud)
			# 募集終了処理を実行する
			await LFGWorker.end_lfg(2, ctx.guild.id, ctx.author.id)
			# 募集終了通知を送信する
			await ctx.respond(embed=embed, ephemeral=True)
		except Exception as e:
			error("- エラー")
			error(traceback.format_exc())
			embed = EmbedTemplate.internal_error
			embed.add_field(name="エラー内容", value=f"```{str(e)}```")
			await ctx.response.send_message(embed=embed, ephemeral=True)

	@lfg.command(description="現在行っているメンバーの募集をキャンセルします。")
	async def cancel(self, ctx: discord.ApplicationContext):
		try:
			# ユーザーデータを取得する
			ud = Data.userdata[ctx.guild.id][ctx.author.id]
			# 埋め込みメッセージを作成
			embed = await self.cancel_embed(ud)
			# 募集終了処理を実行する
			await LFGWorker.end_lfg(2, ctx.guild.id, ctx.author.id)
			# 募集終了通知を送信する
			await ctx.respond(embed=embed, ephemeral=True)
		except Exception as e:
			error("- エラー")
			error(traceback.format_exc())
			embed = EmbedTemplate.internal_error
			embed.add_field(name="エラー内容", value=f"```{str(e)}```")
			await ctx.response.send_message(embed=embed, ephemeral=True)

class ToiregaKitanaiOmisetteIyadayoneView(discord.ui.View):
	@discord.ui.button(label="募集を終了", style=discord.ButtonStyle.red)
	async def end_lfg(self, button, interaction: discord.Interaction):
		# ボタンを削除する
		await self.message.edit(view=None)
		# ユーザーデータを取得する
		ud = Data.userdata[interaction.guild.id][interaction.user.id]
		# 埋め込みメッセージを作成
		embed = await LFG.end_embed(ud)
		# 募集終了通知を送信する
		await interaction.response.send_message(embed=embed, ephemeral=True)
		# 募集終了処理を実行する
		await LFGWorker.end_lfg(1, interaction.guild.id, interaction.user.id)

	@discord.ui.button(label="募集をキャンセル", style=discord.ButtonStyle.blurple)
	async def cancel_lfg(self, button, interaction: discord.Interaction):
		# ボタンを削除する
		await self.message.edit(view=None)
		# ユーザーデータを取得する
		ud = Data.userdata[interaction.guild.id][interaction.user.id]
		# 埋め込みメッセージを作成
		embed = await LFG.cancel_embed(ud)
		# 募集終了通知を送信する
		await interaction.response.send_message(embed=embed, ephemeral=True)
		# 募集終了処理を実行する
		await LFGWorker.end_lfg(2, interaction.guild.id, interaction.user.id)

class LFGView(discord.ui.View):
	@discord.ui.button(label="参加", emoji="✅", style=discord.ButtonStyle.green)
	async def button_callback(self, button, interaction):
		# 募集IDを取得
		try:
			lfgid = int(interaction.message.embeds[0].footer.text.lstrip("ID: "))
		except Exception as e:
			error("- エラー")
			error(traceback.format_exc())
			embed = EmbedTemplate.internal_error
			embed.add_field(name="エラー内容", value=f"```{str(e)}```")
			await interaction.response.send_message(embed=embed, ephemeral=True)
			return

		try:
			ud = Data.userdata[interaction.guild.id][int(lfgid)]
			rmsg = interaction.message
			if type(rmsg) != discord.Message:
				return
		except Exception as e:
			error("- エラー")
			error(traceback.format_exc())
			embed = EmbedTemplate.internal_error
			embed.add_field(name="エラー内容", value=f"```{str(e)}```")
			await interaction.response.send_message(embed=embed, ephemeral=True)

		async def update_member_list():
			try:
				original_embed = rmsg.embeds[0]
			except:
				return

			try:
				for field in original_embed.fields:
					if field.name.startswith(":busts_in_silhouette: 参加者") is True:
						field.name = f":busts_in_silhouette: 参加者 ({len(ud.LFG.Member)}/{ud.LFG.Max_Number_Of_Member + 1})"
						field.value = Util.convert_to_user_bullet_points_from_id_list(ud.LFG.Member)
				await rmsg.edit(rmsg.content, embed=original_embed, view=LFGView(timeout=None))
			except Exception as e:
				error("- エラー")
				error(traceback.format_exc())
				embed = EmbedTemplate.internal_error
				embed.add_field(name="エラー内容", value=f"```{str(e)}```")
				await interaction.response.send_message(embed=embed, ephemeral=True)

		async def send_join_message():
			try:
				# 埋め込みメッセージを作成して返信
				embed = discord.Embed(color=discord.Colour.from_rgb(131, 177, 88))
				embed.set_author(name=f"{interaction.user} さんが参加しました", icon_url=interaction.user.display_avatar.url)
				embed.set_footer(text=f"ID: {lfgid}")
				await interaction.response.send_message(embed=embed)
			except Exception as e:
				error("- エラー")
				error(traceback.format_exc())
				embed = EmbedTemplate.internal_error
				embed.add_field(name="エラー内容", value=f"```{str(e)}```")
				await interaction.response.send_message(embed=embed, ephemeral=True)

		# 募集IDを取得
		try:
			lfgid = int(interaction.message.embeds[0].footer.text.lstrip("ID: "))
		except:
			self.clear_items()
			return
		# 募集者のIDを取得
		author_id = lfgid

		try:
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
						await update_member_list()
						await send_join_message()
						# 募集を締め切る
						await LFGWorker.end_lfg(1, rmsg.guild.id, lfgid)
						return
					else:
						# 募集データにユーザーIDを追加
						ud.LFG.Member.append(interaction.user.id)
						await update_member_list()
						await send_join_message()
		except Exception as e:
			error("- エラー")
			error(traceback.format_exc())
			embed = EmbedTemplate.internal_error
			embed.add_field(name="エラー内容", value=f"```{str(e)}```")
			await interaction.response.send_message(embed=embed, ephemeral=True)

def setup(bot):
	bot.add_cog(Config(bot))
	bot.add_cog(LFG(bot))

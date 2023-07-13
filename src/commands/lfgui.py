import traceback
from logging import error, info, warning

import discord
from discord.commands import Option, SlashCommandGroup
from discord.ext import commands
from discord.interactions import Interaction
from discord.ui.item import Item

import data as Data
import embed as EmbedTemplate


def list_to_selectoptionlist(list: list) -> list[discord.SelectOption]:
	options = []
	for v in list: options.append(discord.SelectOption(label=str(v), value=str(v)))
	return options

class MainView(discord.ui.View):
	def __init__(self):
		super().__init__(timeout=None) # タイムアウトを無効化
		self.add_item(self.StartButton())

	def embed():
		embed = discord.Embed(
			title=":loudspeaker: メンバー募集",
			description = "募集したいゲームとゲームモードを選択して、メンバー募集を開始できます。",
			colour=discord.Colour.from_rgb(217, 47, 152)
		)
		return embed

	def start():
		pass

	class StartButton(discord.ui.Button):
		def __init__(self):
			super().__init__(style=discord.ButtonStyle.green, label="募集を開始", custom_id="LFGUI_Start_Button")

		async def callback(self, interaction: Interaction):
			pass

class GameSelectorView(discord.ui.View):
	def __init__(self):
		self.add_item(self.GameSelect(options=list_to_selectoptionlist(Data.game_title_list.keys())))

	# ゲーム選択リスト
	class GameSelect(discord.ui.Select):
		def __init__(self, options: list[discord.SelectOption] = ...) -> None:
			super().__init__(placeholder="ゲームを選択", custom_id="LFGUI_Game_Select", options=options)

		async def callback(self, interaction: Interaction):
			view = discord.ui.View.from_message(interaction.message, timeout=None)
			# 既存のモード選択リストを、選択されたゲームのモード一覧が選択肢になった選択リストに置き換える
			#if len(view.children) >= 2: view.remove_item(view.children[1])
			#view.add_item(LFGUIView.ModeSelect(options=list_to_selectoptionlist(Data.game_title_list[self.values[0]])))
			mode_select = view.get_item("LFGUI_Mode_Select")
			mode_select.custom_id = "LFGUI_Mode_Select"
			mode_select.options = list_to_selectoptionlist(Data.game_title_list[self.values[0]])
			await interaction.message.edit(view=view)
			# ユーザーデータを取得
			ud = Data.userdata[interaction.guild.id][interaction.user.id]
			# ユーザーの選択中ゲームを選択されたゲームに変える
			ud.LFGUI.Selected_Game = self.values[0]
			await interaction.response.send_message(f"ゲーム **{str(self.values)}** が選択されました。", ephemeral=True, delete_after=5)

class ModeSelectorView(discord.ui.View):
	def __init__(self):
		self.add_item(self.ModeSelect(options=list_to_selectoptionlist(["指定なし"])))

	# モード選択リスト
	class ModeSelect(discord.ui.Select):
		def __init__(self, options: list[discord.SelectOption] = ...) -> None:
			super().__init__(placeholder="モードを選択", custom_id="LFGUI_Mode_Select", options=options)

		async def callback(self, interaction: Interaction):
			# ユーザーデータを取得
			ud = Data.userdata[interaction.guild.id][interaction.user.id]
			# ユーザーの選択中モードを選択されたモードに変える
			ud.LFGUI.Selected_Mode = self.values[0]
			await interaction.response.send_message(f"モード **{str(self.values)}** が選択されました。", ephemeral=True, delete_after=5)

class MainCommands(commands.Cog):
	# コマンドグループを定義する
	lfgui = SlashCommandGroup("lfgui", "LFG UI Commands")

	# コマンドたち
	@lfgui.command(description="メンバー募集UIを作成します。")
	@discord.guild_only()
	@discord.default_permissions(administrator=True)
	async def create(
		self,
		ctx: discord.ApplicationContext,
		channel: Option(
			discord.TextChannel,
			name="テキストチャンネル",
			description="メンバー募集UIを作成するテキストチャンネル"
		)
	):
		try:
			uimsg = await channel.send(embed=MainView.embed(), view=MainView())
			embed = discord.Embed(
				title=":pager: メンバー募集UI",
				description=f"メンバー募集UIを {channel.mention} へ作成しました。\n[メッセージを表示]({uimsg.jump_url})",
				color=discord.Colour.from_rgb(217, 47, 152)
			)
			await ctx.response.send_message(embed=embed, ephemeral=True)
		except Exception as e:
			error("- エラー")
			error(traceback.format_exc())
			embed = EmbedTemplate.internal_error()
			embed.add_field(name="エラー内容", value=f"```{str(e)}```")
			await ctx.response.send_message(embed=embed, ephemeral=True)

def setup(bot):
	bot.add_cog(MainCommands(bot))

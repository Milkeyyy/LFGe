import datetime
from logging import info
from os import environ

from box import Box
from deta import Deta

import bot as Bot

game_title_list = {
	"Rainbow Six Siege": ["ランク", "アンランク", "クイックマッチ", "デスマッチ", "アーケード", "カスタムマッチ", "訓練場"],
	"Apex Legends": [],
	"VALORANT": [],
	"Battlefield 2042": [],
	"Splatoon 3": []
}
default_gamelist_item = {"Role_ID": "0", "Modes": ["指定なし"]}

default_userdata_item = {
	"LFG": {
		"Status": False,
		"ID": 0,
		"Message_ID": 0,
		"Game": "",
		"Member": [],
		"Max_Number_Of_Member": 0,
		"Timeout": datetime.datetime.now()
	},
	"LFGUI": {
		"Selected_Game": "",
		"Selected_Mode": ""
	}
}

# 各データ変数
guilddata = {}
userdata = Box()

# データベース
deta: Deta

# ギルドデータの読み込み
def load_guild_data():
	# グローバル変数宣言
	global guilddata

	guilddata = deta.Base("guilds")


# ギルドデータの確認
def check_guild_data():
	load_guild_data()

	gd = {}
	info("ギルドデータの確認 開始")
	for guild in Bot.Client.guilds:
		info(f"- Guild ID: {guild.id}")
		# すべてのギルドのデータが存在するかチェック、存在しないギルドがあればそのギルドのデータを作成する
		gd = guilddata.get(str(guild.id))
		if gd == None:
			info("-- ギルドデータを作成")
			guilddata.put(default_guilddata_item, str(guild.id))

		gd = guilddata.get(str(guild.id))
		algamelist = list(gd["Game_List"].keys())

		update_list = {}

		# ゲーム一覧にすべてのゲームが存在するかチェック、存在しないゲームがあれば追加する
		info(f"-- ゲーム一覧を確認")
		for game in game_title_list.keys():
			info(f"--- 確認: {game}")
			if game not in algamelist:
				info(f"---- 作成: {game}")
				update_list[f"Game_List.{game}"] = default_gamelist_item
			# ゲーム一覧の項目に存在しない項目があった場合は追加する
			for glk in default_gamelist_item.keys():
				if gd["Game_List"][game].get(glk) == None:
					update_list[f"Game_List.{game}.{glk}"] = default_gamelist_item[glk]
			update_list[f"Game_List.{game}.Modes"] = game_title_list[game]
		if len(update_list) >= 1: guilddata.update(update_list, str(guild.id))

def create_game_list():
	global game_title_list
	global default_gamelist_item
	global gamelist
	global default_guilddata_item
	global guilddata

	gamelist = {}

	for game in game_title_list.keys():
		gamelist[game] = default_gamelist_item
		if len(game_title_list[game]) >= 1:
			gamelist[game]["Modes"] = game_title_list[game]

	default_guilddata_item = {
		"LFG_Channel": "0",
		"Game_List": gamelist
	}

# ユーザーデータを作成
def create_user_data():
	global userdata

	ud = dict()
	for guild in Bot.Client.guilds:
		ud[guild.id] = {}
		for member in guild.members:
			ud[guild.id][member.id] = default_userdata_item

	userdata = Box(ud)


# 新しくサーバーに参加した時のイベント
@Bot.Client.event
async def on_guild_join(guild):
	# ギルドデータを新規作成する
	guilddata.put(default_guilddata_item, str(guild.id))

# ゲーム一覧を作成
create_game_list()

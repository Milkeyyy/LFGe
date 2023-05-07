import bot as Bot

# ユーザーID一覧をユーザー一覧に変換
def convertToUserFromID(id_list):
	user_list = []
	for id in id_list:
		user_list.append(Bot.Client.get_user(id))
	return user_list


# リストを箇条書き化
def convertToBulletPointsFromList(list: list):
	bp = ""
	for index, item in enumerate(list):
		if index == list.count:
			bp = bp + "・" + item.mention
		else:
			bp = bp + "・" + item.mention + "\n"
	return bp


# ユーザーIDリスト → ユーザーオブジェクトリスト → ユーザー名箇条書き化
def convertToUserBulletPointsFromIDList(id_list):
	return convertToBulletPointsFromList(convertToUserFromID(id_list))

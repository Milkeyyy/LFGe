import bot as Bot


# ユーザーID一覧をユーザー一覧に変換
def convert_to_user_from_id(id_list):
	user_list = []
	for id in id_list:
		user_list.append(Bot.Client.get_user(id))
	return user_list


# リストを箇条書き化
def convert_to_bullet_points_from_list(list: list):
	bp = ""
	for index, item in enumerate(list):
		if index == list.count:
			bp = bp + "・" + item.mention
		else:
			bp = bp + "・" + item.mention + "\n"
	return bp


# ユーザーIDリスト → ユーザーオブジェクトリスト → ユーザー名箇条書き化
def convert_to_user_bullet_points_from_id_list(id_list):
	return convert_to_bullet_points_from_list(convert_to_user_from_id(id_list))

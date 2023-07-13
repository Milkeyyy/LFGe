import bot as Bot


# ユーザーID一覧をユーザー一覧に変換
def convert_to_user_from_id(id_list):
	user_list = []
	for id in id_list:
		user_list.append(Bot.Client.get_user(id))
	return user_list


# リストを箇条書き化
def convert_to_bullet_points_from_list(list: list, owner_id):
	bp = ""
	for index, item in enumerate(list):
		# 対象のユーザーが募集者の場合「募集者」表記をつける
		if item == owner_id: mention = f"・<@{item}> **`募集者`**"
		else: mention = f"・<@{item}>"
		if index == list.count:
			bp = bp + mention
		else:
			bp = bp + mention + "\n"
	return bp


# ユーザーIDリスト → ユーザーオブジェクトリスト → ユーザー名箇条書き化
def convert_to_user_bullet_points_from_id_list(id_list, owner_id):
	return convert_to_bullet_points_from_list(id_list, owner_id)

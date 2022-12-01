import datetime
import os

from qts.lib.bttv_pymysql import read_data
from operator import itemgetter


def get_exchange_list(exchange=None):
	""" 交易所--币对"""
	res_exchange, symbol_result = {}, {}
	sql = "select * from t_exchange"
	res_info = read_data(sql=sql)
	for res_one in res_info:
		exchange_name, level = str(res_one["exchange_name"]), str(res_one["exchange_level"])
		ex_id, exchange_id = res_one["ex_id"], res_one["exchange_id"]
		if level == "0":
			if exchange and exchange_name == exchange:
				res_exchange[ex_id] = {
					"id": ex_id,
					"name": exchange_name,
					"exchange_id": exchange_id,
					"children": [],
				}
			if not exchange:
				res_exchange[ex_id] = {
					"id": ex_id,
					"name": exchange_name,
					"exchange_id": exchange_id,
					"children": [],
				}

	for res_two in res_info:
		two_exchange_id = res_two["exchange_id"]
		if two_exchange_id not in res_exchange.keys():
			continue
		parent_result = res_exchange[two_exchange_id]
		if parent_result:
			two_ex_id, two_exchange_name = res_two["ex_id"], res_two["exchange_name"]
			symbol_result[two_ex_id] = {
				"id": two_ex_id,
				"name": two_exchange_name,
				"exchange_id": two_exchange_id,
			}
			parent_result["children"].append(symbol_result[two_ex_id])
	symbol_list = list(res_exchange.values())
	return symbol_list


def get_page_power(role_id, ps_id):
	"""页面--权限控制"""
	deal_info = {}
	sql = "select * from t_permission"
	perm_list = read_data(sql=sql)
	if role_id != 0:
		sql = "select ps_ids from t_role where role_id=%s"
		r_data = [role_id]
		res_list = read_data(sql=sql, data=r_data)
		role_perms = (res_list[0]["ps_ids"] if len(res_list) > 0 else [])
	else:
		role_perms = []

	for perm in perm_list:
		pid, perm_id = int(perm["ps_pid"]), str(perm["id"])
		if pid == int(ps_id) and int(perm["ps_level"]) == 2:
			sql = "select ps_api_action from t_permission_api where ps_id=%s"
			api_data = [perm_id]
			result = read_data(sql=sql, data=api_data)[0]
			if role_id != 0:
				status = (1 if perm_id in role_perms else 0)
			else:
				status = 1
			deal_info[result["ps_api_action"]] = status
	return deal_info


def get_account_list(user_id):
	"""账户列表--权限控制"""
	account_id_list = []
	sql = "select role_id, account_ids from t_user where user_id=%s"
	user_data = [user_id]
	result = read_data(sql=sql, data=user_data)
	if result:
		role_id = result[0]["role_id"]
		account_ids = result[0]["account_ids"]
		if role_id == 0:
			sql = "select account_id from t_account"
			account_list = read_data(sql=sql)
			account_id_list = [x["account_id"] for x in account_list]
		else:
			account_id_list = account_ids.split(",")
	return account_id_list


def get_account_symbol(exchange_keys, symbol_ids):
	"""获取symbol_ids中的权限"""
	exchange_result = {}
	# symbol_ids中有权限时
	# symbol_ids分割为列表时，空字符串会分割成含字符的列表
	if len(symbol_ids) > 1:
		# 处理一级标签
		for sym_one_id in symbol_ids:
			sym_one = int(sym_one_id)
			if sym_one in exchange_keys.keys():
				exchange = exchange_keys[sym_one]
				if str(exchange.exchange_level) == "0":
					exchange_result[exchange.ex_id] = {
						"id": exchange.ex_id,
						"Name": exchange.exchange_name,
						"exchange_id": exchange.exchange_id,
						"children": [],
					}
		# print("--exchange_result--:", exchange_result)
		#   处理二级标签返回结果
		tmp_result = {}
		for sym_two_id in symbol_ids:
			sym_two = int(sym_two_id)
			if sym_two in exchange_keys.keys():
				exchange = exchange_keys[sym_two]
				if str(exchange.exchange_level) == "1":
					# 当二级标签的父级ID不存在exchange_result.keys()时，就不添加
					if exchange.exchange_id not in exchange_result.keys():
						continue
					parent_result = exchange_result[exchange.exchange_id]
					if parent_result:
						tmp_result[exchange.ex_id] = {
							"id": exchange.ex_id,
							"Name": exchange.exchange_name,
							"exchange_id": exchange.exchange_id,
						}
						parent_result["children"].append(tmp_result[exchange.ex_id])
	# exchange_result.values()为dict_values类型
	# 必须转为列表
	exchange_list = list(exchange_result.values())
	return exchange_list


def get_auth_fn(rid, key_role_perms, perm_apis):
	""" 处理菜单"""
	root_perm_result = {}
	# 处理一级菜单
	for one_perm_api in perm_apis:
		if one_perm_api.permissions.ps_level == "0":
			if rid != 0:
				if one_perm_api.ps_id not in key_role_perms.keys():
					continue
			# 判断管理员
			root_perm_result[one_perm_api.ps_id] = {
				"id": one_perm_api.ps_id,
				"authName": one_perm_api.permissions.ps_name,
				"path": one_perm_api.ps_api_path,
				"order": one_perm_api.ps_api_order,
				"children": [],
			}

	# 处理二级菜单
	for two_perm_api in perm_apis:
		if two_perm_api.permissions.ps_level == "1":
			if rid != 0:
				if two_perm_api.ps_id not in key_role_perms.keys():
					continue
			parent_perm_result = root_perm_result[two_perm_api.permissions.ps_pid]
			if parent_perm_result:
				parent_perm_result["children"].append({
					"id": two_perm_api.ps_id,
					"authName": two_perm_api.permissions.ps_name,
					"path": two_perm_api.ps_api_path,
					"order": two_perm_api.ps_api_order,
					"children": [],
				})
	# 排序
	result_info = root_perm_result.values()
	# order:菜单显示排序
	result = sorted(result_info, key=itemgetter("order"))
	return result


def get_permissions_info(perm_keys, perm_ids):
	perm_result = {}
	# perm_ids中有权限时
	# perm_ids分割为列表时，空字符串会分割成含字符的列表
	if len(perm_ids) > 1:
		# 处理一级菜单
		for per_one_id in perm_ids:
			if int(per_one_id) in perm_keys.keys():
				permission = perm_keys[int(per_one_id)]
				if permission.ps_level == "0":
					perm_result[permission.id] = {
						"id": permission.id,
						"authName": permission.ps_name,
						"path": None,
						"children": []
					}

		# 临时存储二级返回结果
		tmp_result = {}
		# 处理二级菜单
		for per_two_id in perm_ids:
			if int(per_two_id) in perm_keys.keys():
				permission = perm_keys[int(per_two_id)]
				if permission.ps_level == "1":
					# 当二级菜单的父级菜单不存在时，就不添加
					if permission.ps_pid not in perm_result.keys():
						continue
					parent_perm_result = perm_result[permission.ps_pid]
					if parent_perm_result:
						tmp_result[permission.id] = {
							"id": permission.id,
							"authName": permission.ps_name,
							"path": None,
							"children": [],
						}
						parent_perm_result["children"].append(tmp_result[permission.id])

		# 处理三级菜单
		for per_three_id in perm_ids:
			if int(per_three_id) in perm_keys.keys():
				permission = perm_keys[int(per_three_id)]
				if permission.ps_level == "2":
					# 当三级菜单的父级菜单不存在时，就不添加
					if permission.ps_pid not in tmp_result.keys():
						continue
					parent_perm_result = tmp_result[permission.ps_pid]
					if parent_perm_result:
						parent_perm_result["children"].append(
							{
								"id": permission.id,
								"authName": permission.ps_name,
								"path": None,
							})
	# permissionsResult.values()为dict_values类型
	# 必须转为列表
	power_list = list(perm_result.values())
	return power_list


def get_permissions_list(api_list):
	key_categories = {}
	# 显示一级
	per_result = {}
	# 处理一级菜单
	for per_api_one in api_list:
		key_categories[per_api_one.ps_id] = per_api_one

		if per_api_one.permissions.ps_level == "0":
			per_result[per_api_one.ps_id] = {
				"id": per_api_one.ps_id,
				"authName": per_api_one.permissions.ps_name,
				"path": per_api_one.ps_api_path,
				"pid": per_api_one.permissions.ps_pid,
				"children": []
			}

	# 临时存储二级返回结果
	tmp_result = {}
	for per_api_two in api_list:
		if per_api_two.permissions.ps_level == "1":
			# 当二级菜单的父级菜单不存在时，就不添加
			if per_api_two.permissions.ps_pid not in per_result.keys():
				continue
			parent_result = per_result[per_api_two.permissions.ps_pid]
			if parent_result:
				tmp_result[per_api_two.ps_id] = {
					"id": per_api_two.ps_id,
					"authName": per_api_two.permissions.ps_name,
					"path": per_api_two.ps_api_path,
					"pid": per_api_two.permissions.ps_pid,
					"children": []
				}
				parent_result["children"].append(tmp_result[per_api_two.ps_id])

	# 处理三级菜单
	for per_api_three in api_list:
		if per_api_three.permissions.ps_level == "2":
			# 当三级菜单的父级菜单不存在时，就不添加
			if per_api_three.permissions.ps_pid not in tmp_result.keys():
				continue
			parent_result = tmp_result[per_api_three.permissions.ps_pid]
			if parent_result:
				parent_result["children"].append({
					"id": per_api_three.ps_id,
					"authName": per_api_three.permissions.ps_name,
					"path": per_api_three.ps_api_path,
					"pid": str(per_api_three.permissions.id) + "," + str(
						key_categories[per_api_three.permissions.id].permissions.id),
				})
	power_list = list(per_result.values())
	return power_list


def paging(page, size, deal_list):
	start = (page - 1) * size
	end = start + size
	total = len(deal_list)
	p_list = deal_list[start: end]
	return total, p_list
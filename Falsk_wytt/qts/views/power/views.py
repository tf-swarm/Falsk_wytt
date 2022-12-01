import datetime
import logging
from flask import request, session, current_app

from qts import db
from qts.lib.check_login import login_check
from qts.models import PermissionApi, Role, Permission
import json
from . import power_blue
from qts.lib.power import get_page_power, get_permissions_info, get_permissions_list


@power_blue.route("/list", methods=['GET'])
@login_check
def get_all_rights():
	response = {
		"status": 0,
		"error": None,
		"data": None,
		"msg": "suc"
	}

	status = request.args.get('status')
	api_list = PermissionApi.query.all()
	if status == "list":
		result = []
		for per_api in api_list:
			result.append({
				"id": per_api.ps_id,
				"authName": per_api.permissions.ps_name,
				"pid": per_api.permissions.ps_pid,
				"level": per_api.permissions.ps_level,
				"path": per_api.ps_api_path
			})
		response.update({"data": result})
	else:
		power_list = get_permissions_list(api_list)
		response.update({"data": power_list})
	return response


@power_blue.route("/roles", methods=["GET", "POST"])
@login_check
def get_roles():
	"""
	获取角色列表
	添加角色
	"""
	response = {
		"status": 0,
		"error": None,
		"data": None,
		"msg": "suc"
	}
	role_id = session.get('role_id')
	if request.method == "GET":
		power_id = request.args.get('power_id')
		# 获取全部角色信息
		roles_list = Role.query.all()
		perm_list = Permission.query.all()
		perm_keys, roles_results = {}, []
		for perm in perm_list:
			perm_keys[perm.id] = perm

		for roles in roles_list:
			roles_result = {}
			perm_ids = roles.ps_ids.split(",")
			roles_result.update({
				"id": roles.role_id,
				"roleName": roles.role_name,
				"roleDesc": roles.role_desc,
				"children": [],
			})
			roles_result["children"] = get_permissions_info(perm_keys, perm_ids)
			roles_results.append(roles_result)
			response.update({"data": roles_results})
	else:
		# 角色的添加
		role_name = request.json.get('roleName')
		role_desc = request.json.get('roleDesc')
		power_id = request.json.get('power_id')
		ps_ids = ""
		role = Role(ps_ids=ps_ids, role_name=role_name, role_desc=role_desc)
		db.session.add(role)
		db.session.commit()

		response.update({"data": {
			"roleId": role.role_id,
			"roleName": role_name,
			"roleDesc": role_desc,
		}})

	if power_id:
		deal_power = get_page_power(role_id, power_id)
	else:
		deal_power = {}
	response.update({"power": deal_power})
	return response


@power_blue.route("/roles_Id", methods=["GET"])
@login_check
def get_roles_id():
	"""
	state:1.根据id查询角色 2.根据id更新角色 3.根据id删除角色
	"""
	response = {
		"status": 0,
		"error": None,
		"data": None,
		"msg": "suc"
	}
	status = request.args.get('status')
	role_id = request.args.get('role_id')
	res = Role.query.filter(Role.role_id == role_id).first()
	if status == "1":
		role_info = {
			"roleId": res.role_id,
			"roleName": res.role_name,
			"roleDesc": res.role_desc,
			"rolePermDesc": res.ps_ca,
		}
		response.update({"data": role_info})
	if status == "2":
		role_desc = request.args.get('roleDesc')
		role_name = request.args.get('roleName')
		res.role_name = role_name
		res.role_desc = role_desc
		db.session.commit()
		roles_info = {
			"roleId": res.role_id,
			"roleName": res.role_name,
			"roleDesc": res.role_desc,
		}
		response.update({"data": roles_info})
	if status == "3":
		Role.query.filter(Role.role_id == role_id).delete()
		db.session.commit()
	return response


@power_blue.route("/delete_role", methods=["POST"])
@login_check
def delete_role_right():
	"""
	删除角色特定权限
	"""
	response = {
		"status": 0,
		"error": None,
		"data": None,
		"msg": "suc"
	}
	role_id = request.json.get('role_id')
	right_id = request.json.get('right_id')
	res = Role.query.filter(Role.role_id == role_id).first()
	ps_ids = res.ps_ids.split(",")
	new_ps_ids = []
	# 存储新的权限
	for ps_id in ps_ids:
		if int(right_id) == int(ps_id):
			continue
		new_ps_ids.append(ps_id)
	# 将权限列表转成用逗号隔开的字符串
	new_ps_ids_str = ",".join(new_ps_ids)
	res.ps_ids = new_ps_ids_str
	# 更新数据库
	db.session.commit()

	# 返回当前角色最新的权限数据
	perm_list = Permission.query.all()
	perm_keys = {}
	# perm 作为value存入字典中
	for perm in perm_list:
		perm_keys[perm.id] = perm
	response.update({"data": get_permissions_info(perm_keys, new_ps_ids)})
	return response


@power_blue.route("/update_role", methods=["POST"])
@login_check
def update_role_right():
	"""
	对角色进行授权
	"""
	response = {
		"status": 0,
		"error": None,
		"data": None,
		"msg": "suc"
	}
	role_str = request.json.get('rids')
	role_id = request.json.get('role_id')
	res = Role.query.filter(Role.role_id == role_id).first()
	res.ps_ids = role_str
	db.session.commit()
	return response





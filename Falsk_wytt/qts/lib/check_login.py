import datetime
from flask import session, jsonify
from functools import wraps


def login_check(func):
	"""
	定义登录注册验证的装饰器
	:return: check_login
	:param func:
	:return:
	"""
	@wraps(func)
	def check_login(*args, **kwargs):
		user_id = session.get('user_id')
		if user_id:
			response = func(*args, **kwargs)
			return jsonify(response)
		else:
			response = {
				'status': 100,
				'error': '未登录',
				'data': None,
				'message': '请登录',
				'timestamp': datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
			}
			return jsonify(response)

	return check_login

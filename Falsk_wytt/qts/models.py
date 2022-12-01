import hashlib
import re

from sqlalchemy.dialects.mysql import BIT

from . import db
from .constants import USERS


class User(db.Model):
	__tablename__ = 't_user'

	user_id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
	name = db.Column(db.String(50), unique=True)
	password = db.Column(db.String(50))
	salt = db.Column(db.String(36))
	role_id = db.Column(db.INTEGER)
	state = db.Column(db.INTEGER)
	mobile = db.Column(db.String(32))
	email = db.Column(db.String(64))
	create_date = db.Column(db.DateTime)
	account_ids = db.Column(db.String(512))

	def to_dict(self):
		resp_dict = {
			'user_id': self.user_id,
			'name': self.name,
			'password': self.password,
			'salt': self.salt,
			'role_id': self.role_id,
			'state': self.state,
			'mobile': self.mobile,
			'email': self.email,
			'account_ids': self.account_ids,
			'create_date': self.create_date.strftime("%Y-%m-%d %H:%M:%S"),
		}
		return resp_dict

	@staticmethod
	def check_password(user, password):
		salt = user.salt
		real_password = user.password
		md_l = hashlib.md5((real_password + salt).encode()).hexdigest()
		m = hashlib.md5()
		m.update((password + salt).encode('utf-8'))
		md = m.hexdigest()
		if md == md_l:
			return True
		else:
			return False

	@staticmethod
	def alter_password(user, password):
		salt = user.salt
		m = hashlib.md5()
		m.update((password + salt).encode('utf-8'))
		md = m.hexdigest()
		user.password = md

	@staticmethod
	def checkio(data):
		return True if re.search(
			r"^[a-zA-Z](?=[a-zA-Z0-9_!@#%\.]*\d)(?=[a-zA-Z0-9_!@#%\.]*[A-Z])(?=[a-zA-Z0-9_!@#%\.]*[a-z])"
			r"(?=[a-zA-Z0-9_!@#%\.]*[_!@#%\.])[a-zA-Z0-9_!@#%\.]{7,15}$",
			data) else False


class Permission(db.Model):
	__tablename__ = 't_permission'

	id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
	ps_name = db.Column(db.String(20))
	ps_pid = db.Column(db.INTEGER)
	ps_c = db.Column(db.String(32))
	ps_a = db.Column(db.String(32))
	ps_level = db.Column(db.String(6))

	def to_dict(self):
		resp_dict = {
			'id': self.id,
			'ps_name': self.ps_name,
			'ps_pid': self.ps_pid,
			'ps_c': self.ps_c,
			'ps_a': self.ps_a,
			'ps_level': self.ps_level,
		}
		return resp_dict


class PermissionApi(db.Model):
	__tablename__ = 't_permission_api'

	id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
	ps_id = db.Column(db.INTEGER, db.ForeignKey("t_permission.id"))
	ps_api_service = db.Column(db.String(255))
	ps_api_action = db.Column(db.String(255))
	ps_api_path = db.Column(db.String(255))
	ps_api_order = db.Column(db.INTEGER)
	permissions = db.relationship("Permission", backref=db.backref("apis"), uselist=False)

	def to_dict(self):
		resp_dict = {
			'id': self.id,
			'ps_api_service': self.ps_api_service,
			'ps_api_action': self.ps_api_action,
			'ps_api_path': self.ps_api_path,
			'ps_api_order': self.ps_api_order,
			'ps_id': self.ps_id,
		}
		return resp_dict


class Role(db.Model):
	__tablename__ = 't_role'

	role_id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
	role_name = db.Column(db.String(20))
	ps_ids = db.Column(db.String(512))
	ps_ca = db.Column(db.Text)
	role_desc = db.Column(db.Text)

	def to_dict(self):
		resp_dict = {
			'role_id': self.role_id,
			'role_name': self.role_name,
			'ps_ids': self.ps_ids,
			'ps_ca': self.ps_ca,
			'role_desc': self.role_desc,
		}
		return resp_dict


class Account(db.Model):
	__tablename__ = 't_account'

	account_id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
	account_name = db.Column(db.String(100))
	exchange = db.Column(db.String(36))
	api_key = db.Column(db.String(255))
	secret_key = db.Column(db.String(255))
	symbol_ids = db.Column(db.String(512))
	create_date = db.Column(db.DateTime)

	def to_dict(self):
		resp_dict = {
			'id': self.account_id,
			'account_name': self.account_name,
			'exchange': self.exchange,
			'api_key': self.api_key,
			'secret_key': self.secret_key,
			'symbol_ids': self.symbol_ids,
			'create_date': self.create_date.strftime("%Y-%m-%d %H:%M:%S"),
		}
		return resp_dict


class OrderBook(db.Model):
	"""铺单策略"""
	__tablename__ = 't_order_book'

	# 价格模式 1-随机波动模式；2-目标价模式；3-跟市模式
	draping_id = db.Column(db.String(50), primary_key=True)
	created_date = db.Column(db.DateTime)
	exchange = db.Column(db.String(36))
	symbol = db.Column(db.String(50))
	is_enabled = db.Column(BIT(1))
	json_info = db.Column(db.String(1600))
	updated_date = db.Column(db.DateTime)
	user_id = db.Column(db.INTEGER)

	def to_dict(self):

		resp_dict = {
			'id': self.draping_id,
			'created_date': self.created_date.strftime("%Y-%m-%d %H:%M:%S"),
			'exchange': self.exchange,
			'symbol': self.symbol,
			'is_enabled': self.is_enabled,
			'json_info': self.json_info,
			'updated_date': self.updated_date.strftime("%Y-%m-%d %H:%M:%S"),
			'user_id': self.user_id,
		}
		return resp_dict


class BrushOrder(db.Model):
	"""对敲策略"""
	__tablename__ = 't_brush_order'

	bucketing_id = db.Column(db.String(50), primary_key=True)
	created_date = db.Column(db.DateTime)
	exchange = db.Column(db.String(36))
	symbol = db.Column(db.String(50))
	is_enabled = db.Column(BIT(1))
	json_info = db.Column(db.String(1600))
	updated_date = db.Column(db.DateTime)
	user_id = db.Column(db.INTEGER)

	def to_dict(self):

		resp_dict = {
			'id': self.bucketing_id,
			'created_date': self.created_date.strftime("%Y-%m-%d %H:%M:%S"),
			'exchange': self.exchange,
			'symbol': self.symbol,
			'is_enabled': self.is_enabled,
			'json_info': self.json_info,
			'updated_date': self.updated_date.strftime("%Y-%m-%d %H:%M:%S"),
			'user_id': self.user_id,
		}
		return resp_dict


class DampingOrder(db.Model):
	"""阻尼挂单"""
	__tablename__ = 't_damping_order'

	damping_order_id = db.Column(db.String(50), primary_key=True)
	created_date = db.Column(db.DateTime)
	exchange = db.Column(db.String(36))
	symbol = db.Column(db.String(50))
	is_enabled = db.Column(BIT(1))
	json_info = db.Column(db.String(1600))
	updated_date = db.Column(db.DateTime)
	user_id = db.Column(db.INTEGER)

	def to_dict(self):

		resp_dict = {
			'id': self.damping_order_id,
			'created_date': self.created_date.strftime("%Y-%m-%d %H:%M:%S"),
			'exchange': self.exchange,
			'symbol': self.symbol,
			'is_enabled': self.is_enabled,
			'json_info': self.json_info,
			'updated_date': self.updated_date.strftime("%Y-%m-%d %H:%M:%S"),
			'user_id': self.user_id,
		}
		return resp_dict


class TradesRecord(db.Model):
	"""成交记录"""
	__tablename__ = 't_trades_record'

	trades_id = db.Column(db.INTEGER, primary_key=True, autoincrement=True)
	account_id = db.Column(db.INTEGER)
	account_name = db.Column(db.String(50))
	insert_date = db.Column(db.DateTime)
	order_id = db.Column(db.String(20))
	symbol = db.Column(db.String(50))
	is_buyer = db.Column(db.INTEGER)
	json_info = db.Column(db.String(1600))

	def to_dict(self):
		resp_dict = {
			'id': self.trades_id,
			'account_id': self.account_id,
			'account_name': self.account_name,
			'insert_date': self.insert_date.strftime("%Y-%m-%d %H:%M:%S"),
			'order_id': self.order_id,
			'symbol': self.symbol,
			'is_buyer': self.is_buyer,
			'json_info': self.json_info,
		}
		return resp_dict


class BalanceCount(db.Model):
	"""账户余额统计"""
	__tablename__ = 't_balance_count'

	balance_id = db.Column(db.INTEGER, primary_key=True)
	insert_date = db.Column(db.DateTime)
	account_id = db.Column(db.INTEGER)
	account_name = db.Column(db.String(50))
	json_info = db.Column(db.String(1600))

	def to_dict(self):

		resp_dict = {
			'id': self.balance_id,
			'insert_date': self.insert_date.strftime("%Y-%m-%d %H:%M:%S"),
			'account_id': self.account_id,
			'account_name': self.account_name,
			'json_info': self.json_info,
		}
		return resp_dict


class CoinHistory(db.Model):
	"""充提币记录"""
	__tablename__ = 't_deposit_withdraw'

	tran_id = db.Column(db.String(20), primary_key=True)
	insert_date = db.Column(db.DateTime)
	account_id = db.Column(db.INTEGER)
	transfer_type = db.Column(db.INTEGER)
	json_info = db.Column(db.String(1600))

	def to_dict(self):

		resp_dict = {
			'id': self.tran_id,
			'insert_date': self.insert_date.strftime("%Y-%m-%d %H:%M:%S"),
			'account_id': self.account_id,
			'transfer_type': self.transfer_type,
			'json_info': self.json_info,
		}
		return resp_dict


class TWAP(db.Model):
	"""时间加权平均价格算法"""
	__tablename__ = 't_TWAP'

	twap_id = db.Column(db.String(50), primary_key=True)
	created_date = db.Column(db.DateTime)
	exchange = db.Column(db.String(36))
	symbol = db.Column(db.String(50))
	is_enabled = db.Column(BIT(1))
	json_info = db.Column(db.String(1600))
	updated_date = db.Column(db.DateTime)
	user_id = db.Column(db.INTEGER)

	def to_dict(self):

		resp_dict = {
			'id': self.twap_id,
			'created_date': self.created_date.strftime("%Y-%m-%d %H:%M:%S"),
			'exchange': self.exchange,
			'symbol': self.symbol,
			'is_enabled': self.is_enabled,
			'json_info': self.json_info,
			'updated_date': self.updated_date.strftime("%Y-%m-%d %H:%M:%S"),
			'user_id': self.user_id,
		}
		return resp_dict


class Exchange(db.Model):
	"""交易所-币种"""
	__tablename__ = 't_exchange'

	ex_id = db.Column(db.INTEGER, primary_key=True)
	exchange_name = db.Column(db.String(50))
	exchange_id = db.Column(db.INTEGER)
	exchange_level = db.Column(db.INTEGER)

	def to_dict(self):
		resp_dict = {
			'id': self.ex_id,
			'exchange_name': self.exchange_name,
			'exchange_id': self.exchange_id,
			'exchange_level': self.exchange_level,
		}

		return resp_dict





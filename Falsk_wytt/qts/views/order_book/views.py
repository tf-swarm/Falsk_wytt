import datetime
import threading
import logging
from flask import request, session, current_app
from sqlalchemy import and_

from qts import db
from qts.lib.check_login import login_check
from qts.lib.time_uuid import create_time_uuid
from qts.models import OrderBook, Account
from . import orderBook_blue
import json
from qts.utils.tool.tool import Time
from qts import redis_deal
from strategy.strategyManager import strategyManager
from qts.lib.power import get_page_power


@orderBook_blue.route("/findPage", methods=['POST'])
@login_check
def find_page():
	response = {
		"status": 0,
		"error": None,
		"data": None,
		"msg": "suc"
	}
	exchange_list, draping_list = [], []
	total = 0
	now_time = datetime.datetime.now()
	start_date = str(datetime.date(2020, 1, 1))
	end_date = str(now_time + datetime.timedelta(seconds=2))
	draping_id = request.json.get('draping_id')
	power_id = request.json.get('power_id')
	page = request.json.get('page')
	size = request.json.get('size')
	sort_ = request.json.get('sort')
	order = request.json.get('order')
	query = request.json.get('query')

	column_dict = {
		'draping_id': OrderBook.draping_id.desc(),
		'created_date': OrderBook.created_date.desc(),
		'updated_date': OrderBook.updated_date.desc(),
		'user_id': OrderBook.user_id.desc(),
	}
	if sort_ in column_dict.keys():
		pass
	else:
		sort_ = 'created_date'

	if draping_id:
		draping = OrderBook.query.filter_by(draping_id=draping_id).first()
		draping_info = draping.to_dict()
		json_info = json.loads(draping_info.get("json_info"))
		pattern = ("随机波动" if json_info["model_type"] == "0" else "目标价" if json_info["model_type"] == "1" else "跟市")
		dra_id, create_time, is_enabled = draping_info.get("id"), draping_info.get("created_date"), draping_info.get("is_enabled")
		buy_amount, sell_amount = list(json_info.get("buy_amount")), list(json_info.get("sell_amount"))
		json_info.update({
			"id": dra_id, "draping_id": dra_id, "is_enabled": is_enabled, "created_date": create_time,
			"pattern": pattern, "buy_start": buy_amount[0], "buy_end": buy_amount[1],
			"sell_start": sell_amount[0], "sell_end": sell_amount[1]
		})
		draping_list.append(json_info)
		total = len(draping_list)
	else:
		if query:
			user_id = query['userId']
			start_time = (query['startDate'] if "startDate" in query else start_date)
			end_time = (query['endDate'] if "endDate" in query else end_date)
			if order == "ASCE":
				draping_data = OrderBook.query.filter(
					and_(OrderBook.user_id == user_id, OrderBook.created_date >= start_time, OrderBook.created_date <= end_time)).order_by(sort_)
			else:
				draping_data = OrderBook.query.filter(and_(OrderBook.user_id == user_id, OrderBook.created_date.__ge__(start_time),
										OrderBook.created_date.__le__(end_time))).order_by(column_dict[sort_])
			if draping_data:
				p_age = draping_data.paginate(page=page, per_page=size)
				total = p_age.total  # 查询返回的记录总数
				draping_data = p_age.items
			for res in draping_data:
				draping_dict = res.to_dict()
				json_info = json.loads(draping_dict.get("json_info"))
				pattern = ("随机波动" if json_info["model_type"] == "0" else "目标价" if json_info["model_type"] == "1" else "跟市")
				dra_id, create_time, is_enabled = draping_dict.get("id"), draping_dict.get("created_date"), draping_dict.get("is_enabled")
				buy_amount, sell_amount = list(json_info.get("buy_amount")), list(json_info.get("sell_amount"))
				json_info.update({
					"id": dra_id, "draping_id": dra_id, "is_enabled": is_enabled, "created_date": create_time,
					"pattern": pattern, "buy_start": buy_amount[0], "buy_end": buy_amount[1],
					"sell_start": sell_amount[0], "sell_end": sell_amount[1]
				})
				draping_list.append(json_info)
		else:
			response['error'] = '参数不全'
	role_id = session.get('role_id')
	if power_id:
		deal_power = get_page_power(role_id, power_id)
	else:
		deal_power = {}
	brush_info = {"total": total, "rows": draping_list}
	response.update({"data": brush_info, "power": deal_power})
	print("--orderBook_response--", response)
	return response


@orderBook_blue.route("/save", methods=["POST"])
@login_check
def save_arguments():
	print("----orderBook_save---:", request.json)
	created_date = datetime.datetime.now()
	stamp = created_date.strftime("%Y%m%d%H%M%S%f")[:-3]
	updated_date = created_date
	response = {
		'status': 0,
		'error': None,
		'data': None,
		'msg': "suc"
	}
	user_id = session.get('user_id')
	draping_id = request.json.get('id')
	account_name = request.json.get('account_name')
	account_id = request.json.get('account_id')  # 下单账户ID
	symbol = request.json.get('symbol')
	buy_start = float(request.json.get('buy_start'))  # 买单数量
	buy_end = float(request.json.get('buy_end'))
	sell_start = float(request.json.get('sell_start'))
	sell_end = float(request.json.get('sell_end'))  # 卖单数量
	buy_depth = request.json.get('buy_depth')
	sell_depth = request.json.get('sell_depth')
	bids_spread = request.json.get('bids_spread')
	asks_spread = request.json.get('asks_spread')
	order_num = request.json.get('order_num')
	delay = request.json.get('delay')
	max_time = request.json.get('max_waitTime')
	min_time = request.json.get('min_waitTime')
	pre_precision = request.json.get('price_precision')
	vol_precision = request.json.get('volume_precision')
	is_enabled = 0

	model_type = (str(request.json.get('model_type')) if request.json.get('model_type') else str(request.json.get('pattern')))
	buy_amount, sell_amount = [buy_start, buy_end], [sell_start, sell_end]
	result = Account.query.filter_by(account_id=account_id).first()
	if not result:
		response.update({"error": "账户不存在", "success": False, "status": 101})
	else:
		exchange = result.exchange
		draping_info = {
			"exchange": exchange, "symbol": symbol, "model_type": model_type, "buy_amount": buy_amount, "delay": float(delay),
			"sell_amount": sell_amount, "account_id": account_id, "account_name": account_name, "asks_spread": float(asks_spread),
			"buy_depth": float(buy_depth), "sell_depth": float(sell_depth), "bids_spread": float(bids_spread),
			"order_num": int(order_num), "max_waitTime": int(max_time), "min_waitTime": int(min_time),
			"price_precision": int(pre_precision), "volume_precision": int(vol_precision),
		}

		if model_type == "0":
			day_rate = request.json.get('day_rate')
			draping_info.update({"day_rate": float(day_rate)})
		elif model_type == "1":
			target_price = request.json.get('target_price')
			volatility = request.json.get('volatility')
			timestamp = request.json.get('end_date')
			end_date = Time.Iso8601_to_str(timestamp)
			draping_info.update({"target_price": float(target_price), "day_rate": float(volatility), "end_date": end_date})
		else:
			trade_filter = request.json.get('order_filter')
			draping_info.update({"order_filter": float(trade_filter)})

		if draping_id:
			try:
				draping = OrderBook.query.filter(OrderBook.draping_id == draping_id).first()
				if draping:
					draping.exchange = exchange
					draping.symbol = symbol
					draping.is_enabled = is_enabled
					draping.json_info = json.dumps(draping_info)
					draping.created_date = draping.created_date
					draping.updated_date = updated_date
					draping.user_id = user_id

					db.session.commit()

					response['success'] = True
					response['response'] = draping_id
				else:
					response['status'] = 104
					response['success'] = False
					response['error'] = "未知ID"
			except Exception as e:
				print(e)
				response['status'] = 101
				response['success'] = False
				response['error'] = e
			finally:
				response['timestamp'] = stamp
		else:
			draping_id = create_time_uuid()
			try:
				draping = OrderBook(
					draping_id=draping_id,
					exchange=exchange,
					symbol=symbol,
					is_enabled=is_enabled,
					json_info=json.dumps(draping_info),
					created_date=created_date,
					updated_date=updated_date,
					user_id=user_id
				)
				db.session.add(draping)
				db.session.commit()

				response['success'] = True
				response['response'] = draping.draping_id
			except Exception as e:
				print(e)
				response['status'] = 101
				response['success'] = False
				response['error'] = e
			finally:
				response['timestamp'] = stamp
	return response


@orderBook_blue.route("/start", methods=['GET'])
@login_check
def start():
	"""随机波动模式 目标价模式 跟市模式"""
	response = {
		'status': 0,
		'error': None,
		'data': None,
		'msg': 'suc'
	}
	user_id = session.get('user_id')
	draping_id = request.args.get('id')
	draping = OrderBook.query.filter(OrderBook.draping_id == draping_id).first()
	if draping:
		if draping.is_enabled == 0:
			is_status = 1
			draping.is_enabled = is_status
			json_info = json.loads(draping.json_info)
			account_id, account_name = json_info.get("account_id"), json_info.get("account_name")
			account = Account.query.filter(Account.account_id == account_id, Account.account_name == account_name).first()
			if account:
				account_info = account.to_dict()
				api_key, secret_key = account_info.get("api_key"), account_info.get("secret_key")
				json_info.update({"strategy_id": draping_id, "api_key": api_key, "secret_key": secret_key})

				strategy = {"{}".format(draping_id): is_status}
				redis_deal.hmset("strategy", strategy)
				print("--start_orderbook--", is_status, json_info)
				strategyManager.run("orderbook", json_info)
				db.session.commit()
				response['status'] = 0
				response['msg'] = '开启成功'
			else:
				response['status'] = 101
				response['msg'] = '下单账户异常'
		else:
			response['status'] = 102
			response['msg'] = '该铺单策略已开启'
	else:
		response['status'] = 104
		response['msg'] = '未知ID'

	return response


@orderBook_blue.route("/stop", methods=['GET'])
@login_check
def stop():
	response = {
		'status': 0,
		'error': None,
		'data': None,
		'msg': 'suc'
	}
	draping_id = request.args.get('id')
	draping = OrderBook.query.filter(OrderBook.draping_id == draping_id).first()
	if draping:
		if draping.is_enabled == 1:
			is_status = 0
			draping.is_enabled = is_status
			db.session.commit()

			strategy = {"{}".format(draping_id): is_status}
			redis_deal.hmset("strategy", strategy)
			response['status'] = 0
			response['msg'] = '关闭成功'
		else:
			response['status'] = 103
			response['msg'] = '该铺单策略已关闭'
	else:
		response['status'] = 104
		response['msg'] = '未知ID'
	return response


@orderBook_blue.route("/remove", methods=['GET'])
@login_check
def remove():
	response = {
		'status': 0,
		'error': None,
		'data': None,
		'msg': 'suc'
	}
	draping_id = request.args.get('id')
	res = OrderBook.query.filter(OrderBook.draping_id == draping_id).first()
	if res:
		is_status = 2
		strategy = {"{}".format(draping_id): is_status}
		redis_deal.hmset("strategy", strategy)
		db.session.delete(res)
		db.session.commit()
		response['response'] = res.draping_id
	else:
		response['status'] = 105
		response['response'] = 'null'
		response['msg'] = '未查询到该条数据'
	return response

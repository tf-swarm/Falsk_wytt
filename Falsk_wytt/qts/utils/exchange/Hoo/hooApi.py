# -*- coding:utf-8 -*-
"""
hoo api

author  : tf
created : 2021-05-11
"""
from typing import Any, Callable, Dict, List, Optional, Tuple
from qts.utils.exchange.Hoo.client import Client
#from client import Client
import time
import random
import threading
import json


class Hoo:

	def __init__(self, api_key: str, secret_key: str, plate: str):
		self.api_key = api_key
		self.secret_key = secret_key
		self.client = Client(api_key=api_key, secret_key=secret_key, plate=plate)
	# 	self.symbol = "STC-USDT"
	# 	self.get_hoo_ws(self.symbol, self.get_hoo_callback)
	#
	# def get_hoo_callback(self, message):
	# 	data = json.loads(message)
	# 	# print("--data-:", data)
	# 	if data.get("bids") and data.get("asks"):
	# 		bids = data["bids"][0]["price"]
	# 		asks = data["asks"][0]["price"]
	# 		print("--message-11-:", bids, asks)
	# 	# self.best_quote.update({"buyprice": bids, "sellprice": asks})
	# 	elif data.get("amount") and data.get("price"):
	# 		last_price = data["price"]
	# 		print("--message-22-:", last_price)

	def get_ticker(self, symbol: str):
		"""
		:param symbol:
		:return:{'buyprice': 13.6342, 'sellprice': 13.6342, 'lastPrice': 13.6342}
		{买一价 卖一价 最后成交价}
		"""
		try:
			ticker = self.client.get_ticker(symbol=symbol)
			#print("--ticker--:", ticker)
			return ticker
		except Exception as e:
			print(e)
			return -1

	def get_order_detail(self, symbol: str, order_id: str):
		"""获取成交明细"""
		try:
			detail = self.client.order_detail_info(symbol=symbol, order_id=order_id)
			return detail
		except Exception as e:
			print(e)
			return -1

	def get_account(self):
		"""获取余额"""
		try:
			balances = self.client.get_accounts()
			#print("--balances--", balances)
			return balances
		except Exception as e:
			print(e)
			return -1

	def get_currency(self, coin):
		try:
			while 1:
				balances = self.get_account()
				if balances == -1:
					time.sleep(2)
					continue
				else:
					for asset in balances:
						if asset['symbol'] == coin:
							return float(asset['amount']) + float(asset['freeze'])
					return 0.0
		except Exception as e:
			print(e)
			return -1

	def Buy(self, symbol: str, price: str, quantity: str):
		"""
		:param symbol:
		:param price:
		:param quantity: 数量
		side: 方向,1买，-1卖
		:return: order_id, trade_no
		"""
		try:
			buy_order = self.client.buy_orders(symbol=symbol, price=price, quantity=quantity, side=1)
			#print("--buy_order--", buy_order)
			return buy_order
		except Exception as e:
			print(e)
			return -1

	def Sell(self, symbol: str, price: str, quantity: str):
		"""
		:param symbol:
		:param price:
		:param quantity: 数量
		side: 方向,1买，-1卖
		:return: order_id, trade_no
		"""
		try:
			sell_order = self.client.sell_orders(symbol=symbol, price=price, quantity=quantity, side=-1)
			#print("--sell_order--", sell_order)
			return sell_order
		except Exception as e:
			print(e)
			return -1

	def get_trades(self, symbol: str):
		"""获取最近成交记录"""
		try:
			trade = self.client.get_trade_info(symbol=symbol)
			#print("--trade--", trade)
			return trade
		except Exception as e:
			print(e)
			return -1

	def get_orders_list(self, symbol):
		"""获取订单列表"""
		try:
			page_num, page_size = 1, 50  # 页码  页大小
			side, start_time, end_time = 0, 1625553349000, 1630910149000
			order_list = self.client.get_order_list(symbol=symbol, pagenum=page_num, pagesize=page_size, side=side,
																								start=start_time, end=end_time
																							)
			return order_list
		except Exception as e:
			print(e)
			return -1

	def get_klines(self, symbol, type="15Min", count=1):
		"""
		获取kline
		:param symbol: BTC-USDT
		:param type: 1Min, 5Min, 15Min, 30Min
		:return:
		"""
		try:
			kline = self.client.get_kline(symbol=symbol, type=type, count=count)
			#print("--kline--", kline)
			return kline
		except Exception as e:
			print(e)
			return None

	def cancel_order(self, symbol: str, order_id: str, trade_no: str):
		"""
		:param symbol:
		:param order_id:
		:param trade_no:
		:return: "msg": "ok"
		"""
		try:
			order = self.client.cancel_orders(symbol=symbol, order_id=order_id, trade_no=trade_no)
			#print("--cancel_order--", order)
			return order
		except Exception as e:
			print(e)
			return None

	def get_orders(self, symbol: str):
		"""
		获取币对当前所有挂单
		:param symbol:
		:return:
		"""
		try:
			orders = self.client.get_last_orders(symbol=symbol)
			#print("--get_orders--", orders)
			return orders
		except Exception as e:
			print(e)
			return None

	def cancel_all_orders(self, symbol: str):
		"""
		:param symbol:
		:return: "msg": "ok"
		"""
		try:
			msg = self.client.cancel_orders_all(symbol=symbol)
			#print("--cancel_all_orders--", msg)
			return msg
		except Exception as e:
			print(e)
			return -1

	def get_ws_loop_tickers(self, symbol: str):
		"""
		loop = asyncio.get_event_loop()
		loop.run_until_complete()
		WebSocket----{买一价 卖一价 最后成交价}
		:param symbol:
		:return: "msg": "ok"
		"""
		try:
			self.client.get_ws_tickers(symbol)
			tickers = self.client.tickers_call_back()
			return tickers
		except Exception as e:
			print(e)
			return -1

	def cancel_orders_timeout(self, symbol, stime=30):
		"""
		轮询撤单
		:param symbol:
		:param stime: 撤单时间间隔
		:return:
		"""
		try:
			now_time = int(time.time())
			orders_list = self.get_orders(symbol)
			#print("--orders_list--:", orders_list)
			if len(orders_list) > 0:
				random.shuffle(orders_list)
				# cancel_list = []
				for order in orders_list:
					create_timestamp = int(int(order["create_at"]) / 1000)
					#print("--create_timestamp--:", now_time, create_timestamp)
					if now_time - create_timestamp >= stime:
						order_id, trade_no = order["order_id"], order["trade_no"]
						self.cancel_order(symbol, order_id, trade_no)
					time.sleep(0.5)
		except Exception as e:
			print(e)
			return -1

	def get_market_depth(self, symbol: str):
		"""
		深度数据
		"""
		try:
			msg = self.client.get_depth_info(symbol=symbol)
			return msg
		except Exception as e:
			print(e)
			return -1

	def get_hoo_ws(self, symbol, callback):
		threading.Thread(target=self.client.start_func_hoo, args=(symbol, callback)).start()

	def make_vol(self, symbol, price, amount, side):
		try:
			if side == 1:
				sell_id, sell_trade_no = self.Sell(symbol, price, amount)
				buy_id, buy_trade_no = self.Buy(symbol, price, amount)
			elif side == 2:
				buy_id, buy_trade_no = self.Buy(symbol, price, amount)
				sell_id, sell_trade_no = self.Sell(symbol, price, amount)
			time.sleep(0.1)
			self.cancel_all_orders(symbol)
		except Exception as e:
			print(e)
			return -1


if __name__ == '__main__':
	# 虎符test
	client_id = "3hLdPrFmtKLPfeRrjXZ8taVWnhgzi9"
	client_key = "VydG48Q7F5fALD2VmJHTCuzrpnLej3D1UsPKaicC6E8cgBu5tM"
	# 虎符1
	# client_id = "V11nrCmJqYpw6hqc5widYoVbMxkZPL"
	# client_key = "vMbeNN7HVygszGDqp8VHwXB5etcaMLoUbUfDPZAt24ivJRR4QF"
	# 虎符2
	# client_id = "5aJKNqunNEQDgHoFLMMWXt1GXy14Wi"
	# client_key = "ZpzFYLw2B41JTf1yakY6hqKD9T4fxP9RLA6JZSgPMFv3SDwnMW"

	# client_id = "mK8VtTfrwxVNbhaAS5FU1jU54P7JDF"
	# client_key = " pBfZ7VYUFP8tf3YWD2baCusJCRrAmJVXgqkn96hrcwPeGNuATH"
	symbol = "WTC-USDT"
	hoo = Hoo(client_id, client_key, 'innovate')
	market = hoo.get_orders_list(symbol)
	print("--market--", market)
	# hoo.get_klines(symbol)
	# hoo.get_sub_tickers(symbol)
	# acc = hoo.get_account()
	# print(acc)
	# buy_id1, buy_trade_no1 = hoo.Buy(symbol, "15.4800", "2")
	# buy_id2, buy_trade_no2 = hoo.Buy(symbol, "15.3800", "1")
	# sell_id1, sell_trade_no1 = hoo.Sell(symbol, "58036.93", "0.001")
	# {'order_id': '11620195555868720', 'trade_no': '40513617039980525003744'}
	# hoo.cancel_order(symbol, '11620195563342721', '40513618515420104020653')
	# hoo.get_account()
	# hoo.cancel_orders_timeout(symbol)
	# hoo.cancel_order(symbol, buy_id1, buy_trade_no1)
	# hoo.cancel_order(symbol, buy_id2, buy_trade_no2)
	# hoo.cancel_all_orders(symbol)

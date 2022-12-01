# -*- coding:utf-8 -*-

import requests
import time
import hmac
import hashlib
import ujson
import random
import string
import websockets
import json
import asyncio
import websocket


class Client:
	API_URL = "https://api.hoo.co"
	WS_URL = "wss://api.hoo.co/ws"
	SERVER_URL = "/open/v1/timestamp"
	DEPTH_URL = "/open/v1/depth"
	TRADE_URL = "/open/v1/tickers/trade"
	DETAIL_URL = "/open/v1/orders/detail"
	BALANCE_URL = "/open/v1/balance"
	PLACE_URL = "/open/v1/orders/place"
	KLINE_URL = "/open/v1/kline"
	CANCEL_URL = "/open/v1/orders/cancel"
	LAST_URL = "/open/v1/orders/last-maker"   # /open/v1/orders/last
	CANCEL_ALL_URL = "/open/v1/orders/batcancel"
	ORDER_LIST_URL = "/open/v1/orders"
	trade_info = {}

	def __init__(self, api_key: str, secret_key: str, plate: str):
		self.API_KEY = api_key
		self.API_SECRET = secret_key

		if plate == 'innovate':
			self.API_URL = "https://api.hoo.co"
			self.WS_URL = "wss://api.hoo.co/ws"
			self.SERVER_URL = "/open/innovate/v1/timestamp"
			self.DEPTH_URL = "/open/innovate/v1/depth"
			self.TRADE_URL = "/open/innovate/v1/tickers/trade"
			self.DETAIL_URL = "/open/innovate/v1/orders/detail"
			self.BALANCE_URL = "/open/innovate/v1/balance"
			self.PLACE_URL = "/open/innovate/v1/orders/place"
			self.KLINE_URL = "/open/innovate/v1/kline/market"
			self.CANCEL_URL = "/open/innovate/v1/orders/cancel"
			self.LAST_URL = "/open/innovate/v1/orders/last"   # /open/v1/orders/last
			self.CANCEL_ALL_URL = "/open/innovate/v1/orders/batcancel"
			self.ORDER_LIST_URL = "/open/innovate/v1/orders"
			self.trade_info = {}

	def nonce_string(self, s_len: int):
		return ''.join(random.sample(string.ascii_letters, s_len))

	def get_timestamp(self):
		requests_url = self.API_URL + self.SERVER_URL
		res = requests.get(requests_url)
		stamp = ujson.loads(res.content)
		return stamp["data"]

	def gen_sign(self, client_id: str, client_key: str):
		ts = int(time.time())
		# server_time = self.get_timestamp()
		nonce = self.nonce_string(5)
		params = {"ts": ts, "nonce": nonce, "sign": "", "client_id": client_id}
		s = "client_id={}&nonce={}&ts={}".format(client_id, nonce, ts)
		v = hmac.new(client_key.encode(), s.encode(), digestmod=hashlib.sha256)
		params["sign"] = v.hexdigest()
		return params

	def login(self):
		ts = int(time.time())
		nonce = self.nonce_string(5)
		obj = {"ts": ts, "nonce": nonce, "sign": "", "client_id": self.API_KEY, "op": "apilogin"}
		s = "client_id=%s&nonce=%s&ts=%s" % (self.API_KEY, nonce, ts)
		v = hmac.new(self.API_SECRET.encode(), s.encode(), digestmod=hashlib.sha256)
		obj["sign"] = v.hexdigest()
		return obj

	def get_ticker(self, **params):
		ticker_info = {}
		try:
			res = self.requests("GET", self.DEPTH_URL, params)
			if res.get("code") == 0 and res.get("data"):
				bids = res["data"]["bids"][0]["price"]
				asks = res["data"]["asks"][0]["price"]
				result = self.get_trade_info(symbol=params["symbol"])
				last_price = result[-1]["price"]
				ticker_info.update({"buyprice": float(bids), "sellprice": float(asks), "lastprice": float(last_price)})
				return ticker_info
			else:
				return res["msg"]
		except Exception as e:
			print(e)
			return -1

	def get_depth_info(self, **params):
		depth_info = {}
		try:
			timestamp = int(time.time() * 1000)
			res = self.requests("GET", self.DEPTH_URL, params)
			if res.get("code") == 0 and res.get("data"):
				bids_list, asks_list = [], []
				for bid, ask in zip(res["data"]["bids"], res["data"]["asks"]):
					bids_list.append([bid["price"], bid["quantity"]])
					asks_list.append([ask["price"], ask["quantity"]])
				depth_info.update({"ts": timestamp, "bids": bids_list, "asks": asks_list})
				return depth_info
			else:
				return res["msg"]
		except Exception as e:
			print(e)
			return -1

	def get_accounts(self):
		try:
			res = self.requests("GET", self.BALANCE_URL)
			if res.get("code") == 0 and res.get("data"):
				balance = filter(lambda x: float(x['amount']) + float(x['freeze']), res["data"])
				return list(balance)
			else:
				return res["msg"]
		except Exception as e:
			print(e)
			return -1

	def order_detail_info(self, **params):
		try:
			res = self.requests("GET", self.DETAIL_URL, params)
			if res.get("code") == 0 and res.get("data"):
				detail = res["data"]
				return detail
			else:
				return res["msg"]
		except Exception as e:
			print(e)
			return -1

	def buy_orders(self, **params):
		try:
			res = self.requests("POST", self.PLACE_URL, params)
			if res.get("code") == 0 and res.get("data"):
				order_id = res["data"]["order_id"]
				trade_no = res["data"]["trade_no"]
				order_info = (order_id, trade_no)
				return order_info
			else:
				print("--buy_orders--:", res["msg"])
				msg = ("0", "0")
				return msg
		except Exception as e:
			print(e)
			return -1

	def sell_orders(self, **params):
		try:
			res = self.requests("POST", self.PLACE_URL, params)
			if res.get("code") == 0 and res.get("data"):
				order_id = res["data"]["order_id"]
				trade_no = res["data"]["trade_no"]
				order_info = (order_id, trade_no)
				return order_info
			else:
				print("--sell_orders--:", res["msg"])
				msg = ("0", "0")
				return msg
		except Exception as e:
			print(e)
			return -1

	def get_trade_info(self, **params):
		try:
			res = self.requests("GET", self.TRADE_URL, params)
			if res.get("code") == 0 and res.get("data"):
				order = res["data"]
				return order
			else:
				return res["msg"]
		except Exception as e:
			print(e)
			return -1

	def get_order_list(self, **params):
		try:
			res = self.requests("GET", self.ORDER_LIST_URL, params)
			if res.get("code") == 0 and res.get("data"):
				order = res["data"]
				return order
			else:
				return res["msg"]
		except Exception as e:
			print(e)
			return -1

	def get_kline(self, **params):
		"""
		获取K线信息
		:param params:
		:return:
		"""
		try:
			res = self.requests("GET", self.KLINE_URL, params)
			if res.get("code") == 0 and res.get("data"):
				order = res["data"][params["count"]-1]
				return order
			else:
				return res["msg"]
		except Exception as e:
			print(e)
			return -1

	def cancel_orders(self, **params):
		try:
			res = self.requests("POST", self.CANCEL_URL, params)
			if res.get("code") == 0 and res.get("msg") == "ok":
				return res["msg"]
			else:
				return res["msg"]
		except Exception as e:
			print(e)
			return -1

	def get_last_orders(self, **params):
		try:
			res = self.requests("GET", self.LAST_URL, params)
			if res.get("code") == 0 and res.get("data"):
				last = res["data"]
				# print("--last_orders--:", last)
				return last
			else:
				return res["msg"]
		except Exception as e:
			print(e)
			return -1

	def cancel_orders_all(self, **params):
		try:
			res = self.requests("POST", self.CANCEL_ALL_URL, params)
			if res.get("code") == 0 and res.get("msg") == "ok":
				return res["msg"]
			else:
				return res["msg"]
		except Exception as e:
			print(e)
			return -1

	async def sub_topic(self, ws, symbol):
		sub = "depth:0:{}".format(symbol)
		await ws.send(json.dumps({"op": "sub", "topic": sub}))

	async def get_sub_topic(self, ws):
		while 1:
			try:
				data_info = await ws.recv()
				data = eval(data_info)
				# print("--data--:", data)
				if data.get("bids") and data.get("asks"):
					bids = data["bids"][0]["price"]
					asks = data["asks"][0]["price"]
				elif data.get("amount") and data.get("price"):
					last_price = data["price"]
				self.trade_info.update({"buyprice": float(bids), "sellprice": float(asks), "lastprice": float(last_price)})
				self.tickers_call_back()
				# print("--ticker_info--:", self.trade_info)

			except websockets.exceptions.ConnectionClosed as e:
				print("connect closed...", e)
				return
			except:
				pass

	async def startup(self, symbol):
		print("start to connect {}..{}".format(self.WS_URL, symbol))
		ws = await websockets.connect(self.WS_URL)
		obj = self.login()
		await ws.send(json.dumps(obj))
		await self.sub_topic(ws, symbol)
		await self.get_sub_topic(ws)

	def get_ws_tickers(self, symbol):
		loop = asyncio.get_event_loop()
		loop.run_until_complete(self.startup(symbol))

	def tickers_call_back(self):
		tickers_info = self.trade_info
		print("--tickers_info--:", tickers_info)
		return tickers_info

	def on_error(self, error):  # 程序报错时，就会触发on_error事件
		print(error)

	def on_close(self):
		print("Connection closed ……")

	def on_open(self):
		"""
		连接到服务器之后就会触发on_open事件，这里用于send数据
		:return:
		"""
		#print("--self.ws--:", self.ws)
		obj = self.login()
		login_info = json.dumps(obj)
		self.ws.send(login_info)
		sub = "depth:0:{}".format(self.symbol)
		self.ws.send(json.dumps({"op": "sub", "topic": sub}))

	def start_func_hoo(self, symbol, callback):
		# while 1:
		try:
			self.symbol = symbol
			websocket.enableTrace(True)
			self.ws = websocket.WebSocketApp(self.WS_URL,
											 on_message=callback,
											 # on_data=on_data,
											 on_error=self.on_error,
											 on_open=self.on_open,
											 on_close=self.on_close, )
			self.ws.run_forever(ping_interval=60, ping_timeout=5)
		except Exception as e:
			print("sub_hoo_ws错误:{}".format(e))
			# time.sleep(5)

	def requests(self, method, url, params=None):
		requests_url = self.API_URL + url
		hoo_info = self.gen_sign(self.API_KEY, self.API_SECRET)
		if params:
			hoo_info.update(params)
		#print("--requests--:", requests_url)
		if method == "GET":
			# print("--GET--:", requests_url, hoo_info)
			res = requests.get(requests_url, params=hoo_info)
		else:
			# print("--POST--:", requests_url, hoo_info)
			res = requests.post(requests_url, data=hoo_info)
		return ujson.loads(res.content)

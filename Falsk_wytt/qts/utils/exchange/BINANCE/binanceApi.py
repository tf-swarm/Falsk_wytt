# -*- coding: UTF-8 -*-
"""
binance api

author  : keyouzhi
created : 2020-06-12
"""
import hmac
import time
import hashlib
import requests
import urllib
import urllib.parse
import urllib.request
import yaml
import datetime
import base64
import json
import random
from qts.utils.exchange.BINANCE.client import Client
from qts.utils.exchange.BINANCE.websockets import BinanceSocketManager


class CBinance():
	"""docstring for CBinance"""
	def __init__(self, akey, skey):
		self.akey = akey
		self.skey = skey

		self.client = Client(api_key=akey, api_secret=skey)
		self.sub_client = BinanceSocketManager(self.client)

	def get_ticker(self,symbol):
		'''
		得到ticker数据
		param symbol
		return {'buyprice': 0.02269, 'sellprice': 0.02284, 'lastprice': 0.02284}
		{买一价 卖一价 最后成交价}
		'''
		try:
			tickers = self.client.get_ticker(symbol = symbol)
			#print(tickers)
		
			ticker = {}
			ticker['buyprice'] = float(tickers['bidPrice'])
			ticker['sellprice'] = float(tickers['askPrice'])
		
			ticker['lastprice'] = float(tickers['lastPrice'])
			return ticker
		except Exception as e:
			print(e)
			return -1

	def get_account(self):
		'''
		获取资产余额
		return [{'asset': 'BNB', 'free': '0.52220109', 'locked': '0.00000000'}, 
				{'asset': 'USDT', 'free': '3.85190000', 'locked': '0.00000000'}, 
				{'asset': 'WTC', 'free': '61.00000000', 'locked': '0.00000000'}]
				[资产 可用数量 冻结数量]
		'''
		try:
			data = self.client.get_account()['balances']
			accs = filter(lambda x: float(x['free']) + float(x['locked']),data)
			return list(accs)
		except Exception as e:
			print(e)
			return -1

	def get_currency(self, coin):
		'''
		获取币资产余额 可用+冻结的
		return 余额
		'''
		try:
			while 1:
				accs = self.get_account()
				if accs == -1:
					time.sleep(2)
					continue
				else:
					for acc in accs:
						if acc['asset'] == coin:
							return float(acc['free']) + float(acc['locked'])
					return 0.0
		except Exception as e:
			print(e)
			return None
	
	def Buy(self, symbol, price, amount):
		'''
		挂买单
		return orderId
		'''
		try:
			print("---Buy---", symbol, price, amount, type(price), type(amount))
			#buyid = self.client.order_limit_buy(symbol=symbol, quantity=str(amount), price=str(price))
			buyid = self.client.order_limit_buy(symbol=symbol, quantity="{:f}".format(amount), price="{:f}".format(price))
		
			return buyid['orderId']
		except Exception as e:
			print(e)
			return -1
		

	def Sell(self, symbol, price, amount):
		'''
		挂卖单
		return orderId 
		'''
		try:
			print("---Sell---", symbol, price, amount, type(price), type(amount))
			# sellid = self.client.order_limit_sell(symbol=symbol, quantity=str(amount), price=str(price))
			sellid = self.client.order_limit_sell(symbol=symbol, quantity="{:f}".format(amount), price="{:f}".format(price))
			return sellid['orderId']
		except Exception as e:
			print(e)
			return -1

	def get_klines(self, symbol, period='15min', count=1):
		"""获取K线信息"""
		try:
			params = {'symbol':symbol, 'interval':period, 'limit':count}
			klines  =self.client.get_klines(symbol=symbol, interval=period, limit=count)
			return klines
		except Exception as e:
			print(e)
			return None

	def cancel_order(self, order_id, symbol):
		'''
		取消订单
		return 状态 ok 
		'''
		try:
			can = self.client.cancel_order(symbol = symbol, orderId = order_id)
			#print(can)
			return can['status']
		except Exception as e:
			print(e)
			return -1

	def get_orders(self,symbol):
		'''
		获取币对当前所有挂单
		return api response
		[
                {
                    "symbol": "LTCBTC",
                    "orderId": 1,
                    "clientOrderId": "myOrder1",
                    "price": "0.1",
                    "origQty": "1.0",
                    "executedQty": "0.0",
                    "status": "NEW",
                    "timeInForce": "GTC",
                    "type": "LIMIT",
                    "side": "BUY",
                    "stopPrice": "0.0",
                    "icebergQty": "0.0",
                    "time": 1499827319559
                }
            ]
		'''
		try:
			orders = self.client.get_open_orders(symbol = symbol)
			#print(orders)
			return orders
		except Exception as e:
			print(e)
			return -1

	def get_trades(self, symbol, startTime=None, endTime=None):
		try:
			if not startTime:
				trades = self.client.get_my_trades(symbol=symbol, limit=1000)
			else:
				trades = self.client.get_my_trades(symbol=symbol, limit=1000, startTime=int(startTime), endTime=int(endTime))
			return trades
		except Exception as e:
			return []

	def cancel_all_orders(self, symbol):
		try:
			can = self.client.cancel_order_all(symbol=symbol)
			return can
		except Exception as e:
			print(e)
			return -1

	def get_sub_deposit_history(self, start_time):
		try:
			deposit_list = []
			for deposit_type in [1, 2]:
				res_list = self.client.get_capital_deposit_hisrec(type=deposit_type, startTime=start_time)
				deposit_list.extend(res_list)
			return deposit_list
		except Exception as e:
			print(e)

	def get_market_depth(self, symbol, limit=20):
		try:
			timestamp = int(time.time() * 1000)
			depth = self.client.get_symbol_depth(symbol=symbol, limit=limit)
			depth.update({"ts": timestamp})
			del depth["lastUpdateId"]
			return depth
		except Exception as e:
			print(e)

	def get_exchangeinfo(self):

		info = self.client.get_exchange_info()
		return info 

	###############################
	#websocket调用接口

	def start(self):
		'''
		开启websocket推送
		'''
		self.sub_client.start()


	def get_depth_ws(self,symbol, callback):
		'''
		获取币对深度
		return 
		{
                "e": "depthUpdate", # Event type
                "E": 123456789,     # Event time
                "s": "BNBBTC",      # Symbol
                "U": 157,           # First update ID in event
                "u": 160,           # Final update ID in event
                "b": [              # Bids to be updated
                    [
                        "0.0024",   # price level to be updated
                        "10",       # quantity
                        []          # ignore
                    ]
                ],
                "a": [              # Asks to be updated
                    [
                        "0.0026",   # price level to be updated
                        "100",      # quantity
                        []          # ignore
                    ]
                ]
            }
		'''
		try:
			self.sub_client.start_depth_socket(symbol, callback, 20)
		except Exception as e:
			print(e)

	def get_ticker_ws(self, symbols, callback):
		'''
		return 
		{
                "e": "24hrTicker",  # Event type
                "E": 123456789,     # Event time
                "s": "BNBBTC",      # Symbol
                "p": "0.0015",      # Price change
                "P": "250.00",      # Price change percent
                "w": "0.0018",      # Weighted average price
                "x": "0.0009",      # Previous day's close price
                "c": "0.0025",      # Current day's close price
                "Q": "10",          # Close trade's quantity
                "b": "0.0024",      # Best bid price
                "B": "10",          # Bid bid quantity
                "a": "0.0026",      # Best ask price
                "A": "100",         # Best ask quantity
                "o": "0.0010",      # Open price
                "h": "0.0025",      # High price
                "l": "0.0010",      # Low price
                "v": "10000",       # Total traded base asset volume
                "q": "18",          # Total traded quote asset volume
                "O": 0,             # Statistics open time
                "C": 86400000,      # Statistics close time
                "F": 0,             # First trade ID
                "L": 18150,         # Last trade Id
                "n": 18151          # Total number of trades
            }
		'''
		try:
			self.sub_client.start_symbol_ticker_socket(symbols, callback)
		except Exception as e:
			print(e)


	def get_trade_list_ws(self, symbols, callback):
		'''
		推送成交记录
		return 
		{
		  "e": "executionReport",        // 事件类型
		  "E": 1499405658658,            // 事件时间
		  "s": "ETHBTC",                 // 交易对
		  "c": "mUvoqJxFIILMdfAW5iGSOW", // clientOrderId
		  "S": "BUY",                    // 订单方向
		  "o": "LIMIT",                  // 订单类型
		  "f": "GTC",                    // 有效方式
		  "q": "1.00000000",             // 订单原始数量
		  "p": "0.10264410",             // 订单原始价格
		  "P": "0.00000000",             // 止盈止损单触发价格
		  "F": "0.00000000",             // 冰山订单数量
		  "g": -1,                       // OCO订单 OrderListId
		  "C": "",                       // 原始订单自定义ID(原始订单，指撤单操作的对象。撤单本身被视为另一个订单)
		  "x": "NEW",                    // 本次事件的具体执行类型
		  "X": "NEW",                    // 订单的当前状态
		  "r": "NONE",                   // 订单被拒绝的原因
		  "i": 4293153,                  // orderId
		  "l": "0.00000000",             // 订单末次成交数量
		  "z": "0.00000000",             // 订单累计已成交数量
		  "L": "0.00000000",             // 订单末次成交价格
		  "n": "0",                      // 手续费数量
		  "N": null,                     // 手续费资产类别
		  "T": 1499405658657,            // 成交时间
		  "t": -1,                       // 成交ID
		  "I": 8641984,                  // 请忽略
		  "w": true,                     // 订单是否在订单簿上？
		  "m": false,                    // 该成交是作为挂单成交吗？
		  "M": false,                    // 请忽略
		  "O": 1499405658657,            // 订单创建时间
		  "Z": "0.00000000",             // 订单累计已成交金额
		  "Y": "0.00000000",              // 订单末次成交金额
		  "Q": "0.00000000"              // Quote Order Qty
		}

		'''
		try:
			self.sub_client.start_user_socket(callback)
		except Exception as e:
			print(e)



if __name__ == '__main__':
	def timestamp_to_str(ts, fmt=None):
		t = time.localtime(ts)
		if fmt is None:
			fmt = '%Y-%m-%d %X'
		return time.strftime(fmt, t)

	# akey = 'FeY0y3dP5HKM4b7X95QBa3ysRDmrWj3Fn9jLJKmqqvgob8FTQHXzQtFBjM68h0pL'
	# skey = 'SO3AgukQpWfdRAyvFyvIg3cVSksDt4sMcNGP8B8S0AZUxd30i9YHucFpQs7vK2JY'

	# akey = 'HctMQ7GbEK6PVd8WRA7ttniwOMVt1N0Q8nO0kcjW6auTKsOPjG19xReiNXmmS7fF'
	# skey = 'DEQUXa3QlQaCZIMHULsLPJNvg2C72pVjLCGxOddWu6pVHuGzAgRSmIKotv36FUeU'
	akey ='DnRX99IIEWSEJfBdi3V2aPoCHN4Az75Oyt2gz1bTP640akmNrjoYPo1gsjgG3CLF'
	skey ='GeUsRhYVgdSQNkl0vX7lHRueU05w75oOIGyR2IcsAI2cghkzSVpYd6Tzuy9slHGF'

	api = CBinance(akey, skey)
	symbol = 'BTCUSDT'
	h_type, start_time = 1, 1631333394*1000  # 1577808000
	history = api.get_sub_deposit_history(start_time)
	print("--history--:", history)
	# for s in history:
	# 	data_info = {}
	# 	date_time = s["time"] / 1000
	# 	# s.update({"date_time": timestamp_to_str(date_time)})
	# 	data_info.update({"date_time": timestamp_to_str(date_time), "counterParty": s["counterParty"],
	# 										"email": s["email"], "type": s["type"], "asset": s["asset"], "qty": s["qty"]})
	# 	print(data_info)
	# from datetime import datetime, date, timedelta
	# yesterday = (date.today() + timedelta(days=-31)).strftime("%Y-%m-%d")
	# print(yesterday, type(yesterday))


	# stime = time.time()
	# buyid = binance.Buy('WTCBNB', 0.01976, 8 )
	# etime = time.time()
	# print(buyid,etime-stime)
	#
	# #buyid = binance.Buy('WTCBNB', 0.02184, 10 )
	# #print(buyid)
	#
	# binance.cancel_all_orders('WTCBNB')

	# depth_list = api.get_market_depth(symbol)
	# print(depth_list)

	# depth_list = api.get_ticker(symbol)
	# {'buyprice': 48808.26, 'sellprice': 48808.27, 'lastprice': 48808.27}
	# print(depth_list)
	
	acc = api.get_account()
	# [{'asset': 'BNB', 'free': '27.36479274', 'locked': '0.00000000'}, {'asset': 'USDT', 'free': '662.17462080', 'locked': '0.00000000'}]
	print('acc:', acc)


	# res = binance.get_currency('USDT')
	# print(res)

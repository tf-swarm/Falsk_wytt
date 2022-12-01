# -*- coding: UTF-8 -*-
"""
阻尼挂单V1.1

author  : keyouzhi
created : 2020-12-8
"""
import sys
import yaml
import time
import os
from os.path import dirname

import random
import numpy as np
import pandas as pd
import datetime
import threading
import configparser

from concurrent import futures
from concurrent.futures.thread import ThreadPoolExecutor
executor_ = ThreadPoolExecutor(max_workers=10)

from qts.utils.quotation.quotApi import QuotApi
from qts.utils.exchange.TAIBI.taibiApi import CTB
from qts.utils.exchange.BINANCE.binanceApi import CBinance
from qts.utils.exchange.BITHUMB.bithumbApi import CBithumb

from qts.utils.util.InitLog import init_log
from qts.utils.util.DataUtility import *

import logging

logging.getLogger('requests').setLevel(logging.ERROR)
logging.getLogger('connectionpool').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)

Logging = logging.getLogger()

init_log("DampingOrderV1.1")

#铺盘口
class CDampingOrder(threading.Thread):
	"""docstring for CMarker"""
	def __init__(self, params):
		threading.Thread.__init__(self)
		self.ini_path = os.path.join(os.path.dirname(__file__), 'orderIds.ini')
		self.config = configparser.ConfigParser()
		self.config.read(self.ini_path)

		self.exchange = params['exchange']
		self.api_key, self.secret_key = params["api_key"], params["secret_key"]
		self.hold_risk_aversion, self.target_hold_qty = params['hold_risk_aversion'], params['target_hold_qty']
		self.amount = [params['min_order_qty'], params['max_order_qty']]
		self.bestPrice_Bias, self.priceRange = params['best_price_bias'], params['price_range']
		self.ordernum = params['order_count']
		self.pricePrecision, self.amountPrecision = params['price_precision'], params['volume_precision']
		symbol = params['symbol']
		if self.exchange == "TAIBI":
			self.api 		= CTB(self.api_key, self.secret_key)
			self.symbol 	= symbol
		elif self.exchange == "BINANCE":
			self.api 		= CBinance(self.api_key, self.secret_key)
			self.symbol 	= symbol.replace('/','')
		elif self.exchange == "BITHUMB":
			self.api 		= CBithumb(self.api_key, self.secret_key)
			self.symbol		= symbol[:symbol.find('/')]

		self.tradeCoin = symbol[:symbol.find('/')]
		self.active = True

		self.orderIds = []


	def updata_ini(self, section, key, orderIds):
		try:
			inifile = open(self.ini_path, 'r+')
			self.config.set(section, key, orderIds)
			self.config.write(inifile)
			inifile.close()
		except Exception as e:
			Logging.exception('update_ini error:{}'.format(e))

	def read_ini(self, section, key):
		try:
			return self.config.get(section, key)
		except Exception as e:
			Logging.exception('read_ini error:{}'.format(e))

	def get_reservation(self):
		try:
			res = self.api.get_klines(self.symbol, '15m', 40)
			klines = res[-31:-1]

			df = pd.DataFrame(klines)
			closestr = df[4].values
			close = closestr.astype(float)

			acc = self.api.get_currency(self.tradeCoin)
			resvPrice = np.mean(close) * (1 - 2 * (self.target_hold_qty - acc) / (self.amount[0] + self.amount[1]) * self.hold_risk_aversion)
			return resvPrice
		except Exception as e:
			print(e)
			return None
	
		# 批量下买单
	def batch_buy(self, os:[]):
		'''
		批量下买单，有时间间隔
		'''
		b_os = []
		try:
			if os:
				for i in range(len(os)):
					buyid = self.api.Buy(self.symbol, os[i][0], os[i][1])
					b_os.append(buyid)
					if buyid != -1:
						self.orderIds.append(buyid)
					time.sleep(2)
			Logging.info('b_os:{}'.format(b_os))
			return b_os
		except Exception as e:
			Logging.exception('批量下买单错误：{}'.format(e))
			return -1

		# 批量下卖单
	def batch_sell(self, os:[]):
		'''
		批量下卖单，每单间有时间间隔
		'''
		s_os = []
		try:
			if os:
				for i in range(len(os)):
					sellid = self.api.Sell(self.symbol, os[i][0], os[i][1])
					s_os.append(sellid)
					if sellid != -1:
						self.orderIds.append(sellid)
					time.sleep(2)
			Logging.info('s_os:{}'.format(s_os))
			return s_os
		except Exception as e:
			Logging.exception('批量下卖单错误：{}'.format(e))
			return -1

	def updata_orderbook(self):
		'''
		得到铺单列表
		return 要铺的单子列表
		'''
		try:
			self.orderIds = eval(self.read_ini('orders', 'orderIds'))
			resvPrice = self.get_reservation()
			ticker = self.api.get_ticker(self.symbol)

			askprice = max(resvPrice*(1+self.bestPrice_Bias), 1.01*ticker['buyprice'])
			bidprice = min(resvPrice*(1-self.bestPrice_Bias), 0.99*ticker['sellprice'])

			interval = self.priceRange / self.ordernum
			def get_buyprice():
				buyprice = [bidprice]
				for i in range(self.ordernum-1):
					newprice = np.random.uniform(bidprice*(1-interval*(i+1) - 0.1*interval), bidprice*(1-interval*(i+1)+ 0.1*interval))
					buyprice.append(newprice)
				return np.array(buyprice)

			def get_sellprice():
				sellprice = [askprice]
				for i in range(self.ordernum-1):
					newprice = np.random.uniform(askprice*(1+interval*(i+1)- 0.1*interval), askprice*(1+interval*(i+1)+ 0.1*interval) )
					sellprice.append(newprice)
				return np.array(sellprice)

			buypricelist = np.round(get_buyprice(), self.pricePrecision)
			sellpricelist = np.round(get_sellprice(), self.pricePrecision)

			buyamountlist = np.round(np.random.uniform(self.amount[0], self.amount[1], self.ordernum), self.amountPrecision)
			sellamountlist = np.round(np.random.uniform(self.amount[0], self.amount[1], self.ordernum), self.amountPrecision)
			
			f = executor_.submit(self.batch_buy, list(zip(buypricelist,buyamountlist)))
			f1 = executor_.submit(self.batch_sell, list(zip(sellpricelist,sellamountlist)))
			futures.wait([f,f1], timeout = 150)
			if not f.done():
				Logging.error('任务f{}超时'.format(f))
				f.cancel()
			if not f1.done():
				Logging.error('任务f1{}超时'.format(f1))
				f1.cancel()
			self.updata_ini('orders', 'orderIds', str(self.orderIds))
		except Exception as e:
			Logging.exception('updata_orderbook:{}'.format(e))
			return -1

	def set_active(self):
		self.active = False

	def cancel_orders(self):
		try:
			orderIds = eval(self.read_ini('orders', 'orderIds'))
			random.shuffle(orderIds)

			print("orderIds before:", orderIds)
			os = []
			for i in range(len(orderIds)):
				res = self.api.cancel_order(orderIds[i], self.symbol)
				if res == -1:
					os.append(orderIds[i])
				time.sleep(3)
			print('os:', os, str(os))
			self.updata_ini('orders', 'orderIds', str(os))

		except Exception as e:
			Logging.exception('cancel_orders:{}'.format(e))

	def run(self):
		while self.active:
			self.cancel_orders()
			self.updata_orderbook()
			time.sleep(900)
		#self.cancel_orders()


if __name__ == '__main__':
	params = {
		 'exchange': 'BINANCE',
		 'symbol': 'WTC/USDT',
		 'member_id': '20201209',
		 'hold_risk_aversion': 0.0,
		 'target_hold_qty': 100,
		 'min_order_qty': 40,
		 'max_order_qty': 50,
		 'best_price_bias': 0.03,
		 'price_range': 0.12,
		 'order_count': 5,
		 'price_precision': 4,
		 'volume_precision': 2,
		 'api_key': 'igSMPclD3fA2WTT7r14DZp75GSzAzu9oAHpLNDjRSAcvszTux8ed891U5faf7C9N',
		 'secret_key': 'wHsYPXKtjKj99REjrJk5cdwmKzQzP9EDdHEs1uqjQSjBzhndpAUeNXUr43JEywYQ'
		}

	obj = CDampingOrder(params)
	obj.start()
	#MarketMaker.start()



	#print(MarketMaker.get_orderlist())
	#MarketMaker.start()

	#MarketMaker.cancelorders_timeout()

	#print(MarketMaker.get_orderlist())
	
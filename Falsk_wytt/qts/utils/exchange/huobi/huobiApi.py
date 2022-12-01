from qts.utils.exchange.huobi.requstclient import RequestClient
from qts.utils.exchange.huobi.subscriptionclient import SubscriptionClient
import time
import datetime


class CHuobi(object):
	"""docstring for CHuobi"""
	def __init__(self, akey, skey):
		self.akey = akey
		self.skey = skey

		self.client = RequestClient(api_key=self.akey, secret_key=self.skey)

		self.sub_client = SubscriptionClient(api_key=self.akey, secret_key=self.skey)



	def get_ticker(self,symbol):
		'''
		得到ticker数据
		param symbol
		return {'buyprice': 0.02269, 'sellprice': 0.02284, 'lastprice': 0.02284}
		return {买一价 卖一价 最后成交价}
		'''

		try:
			tickers = self.client.get_best_quote(symbol)
			ticker = {}
			ticker['buyprice'] = float(tickers.bid_price)
			ticker['sellprice'] = float(tickers.ask_price)
			ticker['lastprice'] = float(tickers.last_price)
			return ticker
		except Exception as e:
			print(e)
			return -1

	def get_all_tickers(self):
		"""
		所有交易对的最新 Tickers
		"""
		try:
			tickers = {}
			res = self.client.get_market_tickers()
			for t in res:
				tickers[t.symbol.upper()] = {'ask': t.ask, 'bid': t.bid, 'close': t.close}
			return tickers
		except Exception as e:
			print(e)
			return -1

	def get_best_quote(self, symbol):
		'''
		return 
		{
		'bid_price': 0.5787, 
		'bid_amount': 516.79, 
		'ask_price': 0.5808, 
		'ask_amount': 16.1409, 
		'last_price': 0.5806
		}
		'''
		try:
			quote = {}
			tickers = self.client.get_best_quote(symbol)
			quote['bid_price'] = float(tickers.bid_price)
			quote['bid_amount'] = float(tickers.bid_amount)
			quote['ask_price'] = float(tickers.ask_price)
			quote['ask_amount'] = float(tickers.ask_amount)
			quote['last_price'] = float(tickers.last_price)
			return quote
		except Exception as e:
			print('get_best_quote error',e)
			return -1

	def get_klines(self, symbol, period='15min', count=10):

		try:
			klines = self.client.get_latest_candlestick(symbol, period, count)

			ks = []
			for i in range(len(klines)):
				a = [0]*5
				a[1] = klines[i].open 
				a[2] = klines[i].high
				a[3] = klines[i].low
				a[4] = klines[i].close
				a[0] = klines[i].id
				ks.append(a)

			return ks[::-1]
		except Exception as e:
			print(e)
			return None

	def get_accounts(self):
		'''
		获取资产余额
		return [{'asset': 'BNB', 'free': '0.52220109', 'locked': '0.00000000'}, 
				{'asset': 'USDT', 'free': '3.85190000', 'locked': '0.00000000'}, 
				{'asset': 'WTC', 'free': '61.00000000', 'locked': '0.00000000'}]
				[资产 可用数量 冻结数量]
		'''
		try:
			accs  = self.client.get_account_balance_by_account_type('spot')
			balances = []
			#print(accs.balances)
			for acc in accs.balances:
				balance = {}
				if float(acc.balance) > 0 and acc.balance_type == 'trade':
					balance['asset'] = acc.currency.upper()
					balance['free'] = acc.balance
					balance['locked'] = 0.0

					for acc in accs.balances:
						if acc.currency.upper() == balance['asset'] and acc.balance_type == 'frozen': 
							balance['locked'] = acc.balance

					balances.append(balance)
			return balances

		except Exception as e:
			print(e)
			return -1

	def get_currency(self, coin):
		'''
		获取币资产余额 可用+冻结的
		'''
		try:
			while 1:
				accs = self.get_accounts()
				if accs == -1:
					time.sleep(2)
					continue
				else:
					for acc in accs:
						if acc['asset'] == coin:
							return float(acc['free']) + float(acc['locked'])
					return 0.0
		except Exception as e:
			return -1

	def withdraw(self, address, amount, currency):
		try:
			withdrawId = self.withdraw(address, amount, currency)
			return withdrawId
		except Exception as e:
			raise e

	
	def Buy(self, symbol, price, amount):
		'''
		挂买单
		return orderId
		'''
		try:
			buyid = self.client.create_order(symbol,'spot','buy-limit',amount,price)
		
			return buyid
		except Exception as e:
			print(e)
			return -1

	def Sell(self, symbol, price, amount):
		'''
		挂卖单
		return orderId 
		'''
		try:
			sellid = self.client.create_order(symbol,'spot','sell-limit',amount,price)
		
			return sellid
		except Exception as e:
			print(e)
			return -1

	def cancel_order(self,order_id,symbol=''):
		'''
		取消订单
		return 状态 ok 
		'''
		try:
			can = self.client.cancel_order(order_id)
			return can
		except Exception as e:
			print(e)
			return -1

	def get_orders(self,symbol):
		'''
		获取当前未成交委托单
		return Order
			self.account_type = AccountType.INVALID
	        self.amount = 0.0
	        self.price = 0.0
	        self.created_timestamp = 0
	        self.canceled_timestamp = 0
	        self.finished_timestamp = 0
	        self.order_id = 0
	        self.symbol = ""
	        self.order_type = OrderType.INVALID
	        self.filled_amount = 0.0
	        self.filled_cash_amount = 0.0
	        self.filled_fees = 0.0
	        self.source = OrderSource.INVALID
	        self.state = OrderState.INVALID
	        self.client_order_id = ""
	        self.stop_price = ""
	        self.next_time = 0
	        self.operator=""
		'''
		try:
			orders = self.client.get_open_orders(symbol)
			os = []
			if len(orders) != 0:
				for i in range(len(orders)):
					o = {}
					o['symbol'] = orders[i].symbol
					o['orderId'] = orders[i].order_id
					o['price'] = orders[i].price
					o['amount'] = orders[i].amount
					o['time'] = orders[i].created_timestamp
					os.append(o)
			return os
		except Exception as e:
			print(e)
			return -1

	def get_order(self, orderId, symbol = ''):
		'''
		return 
		{
		'order_id': 82275055789410, 
		'side': 'buy-limit', 
		'price': 0.3323, 
		'volume': 20.0, 
		'trade_volume': 0.0, 
		'timestamp': 1597739590246
		}
		'''
		try:
			order = self.client.get_order(symbol, orderId)
			orderinfo = {}
			orderinfo['order_id'] = orderId
			orderinfo['side'] = order.order_type
			orderinfo['price'] = float(order.price)
			orderinfo['volume'] = float(order.amount)
			orderinfo['trade_volume'] = float(order.filled_amount)
			orderinfo['timestamp'] = order.created_timestamp

			#order.print_object()
			return orderinfo
		except Exception as e:
			print('get_order error')
			return -1

	def cancel_all_orders(self,symbol):
		try:
			orders = self.get_orders(symbol)
			if orders:
				for o in orders:
					self.cancel_order(o['orderId'])
			return 0
		except Exception as e:
			print(e)
			return -1

	def get_trades(self, symbol, start_time):
		"""历史成交记录"""
		try:
			trades_list = self.client.get_trades_list(symbol=symbol, start_time=start_time)
			return trades_list
		except Exception as e:
			print(e)
			return []

	def get_market_depth(self, symbol):
		try:
			result = self.client.get_price_depth(symbol=symbol)
			bids_list, asks_list = [], []
			for bid, ask in zip(result.bids, result.asks):
				bids = [bid.price, bid.amount]
				asks = [ask.price, ask.amount]
				bids_list.append(bids)
				asks_list.append(asks)
			depth_info = {"ts": result.timestamp, "bids": bids_list, "asks": asks_list}
			return depth_info
		except Exception as e:
			print(e)
			return -1


	###################################
	#websocket调用接口

	def error(e:'HuobiApiException'):
		print(e.error_code + e.error_message)

	def get_trade_list_ws(self, symbols, callback):
		'''
		return 
		{
		    "ch": "trade.clearing#btcusdt#0",
		    "data": {
		         "eventType": "trade",
		         "symbol": "btcusdt",
		         "orderId": 99998888,
		         "tradePrice": "9999.99",
		         "tradeVolume": "0.96",
		         "orderSide": "buy",
		         "aggressor": true,
		         "tradeId": 919219323232,
		         "tradeTime": 998787897878,
		         "transactFee": "19.88",
		         "feeDeduct ": "0",
		         "feeDeductType": "",
		         "feeCurrency": "btc",
		         "accountId": 9912791,
		         "source": "spot-api",
		         "orderPrice": "10000",
		         "orderSize": "1",
		         "clientOrderId": "a001",
		         "orderCreateTime": 998787897878,
		         "orderStatus": "partial-filled"
		    }
		}
		'''
		try:
			self.sub_client.subscribe_trade_clearing_event(symbols, callback)
		except Exception as e:
			raise e

	def get_ticker_ws(self, symbols, callback):
		'''
		return 
		{
		  "ch": "market.btcusdt.bbo",
		  "ts": 1489474082831, //system update time
		  "tick": {
		    "symbol": "btcusdt",
		    "quoteTime": "1489474082811",
		    "bid": "10008.31",
		    "bidSize": "0.01",
		    "ask": "10009.54",
		    "askSize": "0.3",
		    "seqId":"10242474683"
		  }
		}
		'''
		try:
			self.sub_client.subscribe_price_depth_bbo_event(symbols, callback)
			#print(ticker.bid,ticker.bid_size, ticker.ask,ticker.ask_size)
		except Exception as e:
			raise e



#36101396489779
if __name__ == '__main__':
	#KeWTC136
	# access_key = '1qdmpe4rty-e154baec-811787dd-8b9fb'
	# secret_key = '039e93c4-5315c4bc-4fc1a6a5-8e83e'

	access_key = '2a2c3dd4-de856dba-37fd23f7-vf25treb80'
	secret_key = '209ca4c3-eb577629-fde1b295-0eec1'

	api = CHuobi(access_key, secret_key)
	# op_type = "deposit"  # deposit 或 withdraw
	# res = api.get_sub_user_list()
	# print("--res--", res)
	# def str_to_timestamp(s, fmt=None):
	# 	if fmt is None:
	# 		fmt = '%Y-%m-%d %X'
	# 	t = datetime.datetime.strptime(s, fmt).timetuple()
	# 	return int(time.mktime(t))
	#
	# def getdate(day):
	# 	today = datetime.datetime.now()
	# 	# 计算偏移量
	# 	offset = datetime.timedelta(days=-day)
	# 	# 获取想要的日期的时间
	# 	re_date = (today + offset).strftime('%Y-%m-%d')
	# 	return re_date
	#
	# start = getdate(120)
	# end = time.strftime("%Y-%m-%d", time.localtime())
	# print(start, end)
	# date_start = datetime.datetime.strptime(start, '%Y-%m-%d')
	# date_end = datetime.datetime.strptime(end, '%Y-%m-%d')
	#
	# while date_start < date_end:
	# 	date_start += datetime.timedelta(days=1)
	# 	str_time = date_start.strftime('%Y-%m-%d') + " 00:00:00"
	# 	# print(str_time)
	# 	stamp_time = str_to_timestamp(str_time) * 1000
	# 	print(stamp_time)
	# 	symbols, start_time, end_time = "shibusdt", 1621094400000, 1618882225000
	# 	tickers = api.get_trades(symbols, stamp_time)
	# 	# print(tickers)
	# 	if len(tickers) > 0:
	# 		for s in tickers:
	# 			print(s)
	# 	print(str_time)
	# symbols, start_time, end_time = "shibusdt", 1621094400000, 1621180800000
	# tickers = api.get_trades(symbols, start_time)
	# {
	# 	'id': 28342981,
	# 	'symbol': 'shibusdt',
	# 	'orderId': 277494943232318,
	# 	'price': '0.00001631',
	# 	'isBuyer': 'maker',
	# 	'qty': '356645.07',
	# 	'commission': '713.29014',
	# 	'commissionAsset': 'shib',
	# 	'time': 1621222391099
	# }
	# print("--tickers--", tickers)

	# def trade_info(msg):
	# 	# self.ask = 0.0
	# 	# self.ask_size = 0.0
	# 	# self.bid = 0.0
	# 	# self.bid_size = 0.0
	# 	# self.quote_time = 0
	# 	# self.symbol = ""
	# 	print("--msg--", msg.data.ask, msg.data.ask_size, msg.data.quote_time, msg.data.symbol)
	#
	# api.get_ticker_ws(symbols, trade_info)


	# buyid = huobi.Buy('wtcusdt',0.3644, 20)
	# print(buyid)
	# buyid = huobi.Sell('wtcusdt',0.3644, 20)
	# print(buyid)

	#orders = huobi.cancel_all_orders('wtcusdt')
	#print(orders,orders[0].order_id)
	symbol = "btcusdt"
	# ticker_list = api.get_all_tickers()
	# print(ticker_list)

	# depth = api.get_market_depth(symbol)
	# print(depth)

	user = api.get_accounts()
	print(user)
	# depth = api.get_ticker(symbol)
	# print(depth)


	# buyprice, sellprice, lastprice = res["bid"], res["ask"], res["close"]
	# ticker_info = {'buyprice': buyprice, 'sellprice': sellprice, 'lastprice': lastprice}
	# print(ticker_info)

	# res = api.get_currency('WTC')
	# print(res)

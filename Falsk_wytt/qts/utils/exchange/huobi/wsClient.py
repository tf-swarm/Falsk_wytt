from qts.utils.exchange.huobi.subscriptionclient import SubscriptionClient
from qts.utils.exchange.huobi.requstclient import RequestClient
from threading import Thread
from qts.utils.tool.tool import Time
import json


class HuoBiWsClient:
	def __init__(self, param):
		self.api_key = ""  # param["api_key"]
		self.api_secret = ""  # param["api_secret"]
		self.symbols = param["symbol"]
		self.limit = param["limit"]
		# 当type值为‘step0’时，默认深度为150档; 当type值为‘step1’,‘step2’,‘step3’,‘step4’,‘step5’时，默认深度为20档
		self.depth_step = "step1"
		self.client = RequestClient(api_key=self.api_key, secret_key=self.api_secret)
		self.sub_client = SubscriptionClient(api_key=self.api_key, secret_key=self.api_secret)

	def depth_message(self, msg):
		try:
			from qts import redis_deal
			# result = redis_deal.hmget("HUOBI", ["DEPTH"])
			# depth = (eval(result[0]) if result[0] else {})
			# if self.symbols not in depth:
			# 	depth[self.symbols] = {}

			data = redis_deal.hget('HUOBI', 'depth')
			result = (json.loads(data) if data else {})
			if self.symbols not in result:
				result[self.symbols] = {}

			bids_list, asks_list = [], []
			bids = msg.data.bids
			for bid in bids:
				bids_info = {"price": bid.price, "amount": bid.amount}
				bids_list.append(bids_info)

			asks = msg.data.asks
			for ask in asks:
				asks_info = {"price": ask.price, "amount": ask.amount}
				asks_list.append(asks_info)
			depth_info = {"asks": asks_list, "bids": bids_list, "time": Time.current_ms()}

			result[self.symbols].update(depth_info)

			# redis_deal.hmset("HUOBI", {"DEPTH": depth})
			depth_info = json.dumps(result)
			redis_deal.hset("HUOBI", 'depth', depth_info)
		except Exception as e:
			print(e)

	def ticker_message(self, msg):
		try:
			from qts import redis_deal
			# result = redis_deal.hmget("HUOBI", ["DEPTH"])
			# depth = (eval(result[0]) if result[0] else {})
			# if self.symbols not in depth:
			# 	depth[self.symbols] = {}

			data = redis_deal.hget('HUOBI', 'ticker')
			result = (json.loads(data) if data else {})
			if self.symbols not in result:
				result[self.symbols] = {}

			buy_price, sell_price = float(msg.data.bid), float(msg.data.ask)
			last_price = (buy_price + sell_price) / 2
			ticker = {"buy_price": buy_price, "sell_price": sell_price, "last_price": last_price}
			if "ticker" not in result[self.symbols]:
				result[self.symbols]["ticker"] = {}
			result[self.symbols]["ticker"].update(ticker)

			# redis_deal.hmset("HUOBI", {"DEPTH": depth})
			ticker_info = json.dumps(result)
			redis_deal.hset("HUOBI", 'ticker', ticker_info)
		except Exception as e:
			print(e)

	def get_depth_socket(self):
		try:
			self.sub_client.subscribe_price_depth_event(self.symbols, self.depth_step, self.depth_message)
		except Exception as e:
			print(e)

	def get_ticker_socket(self):
		try:
			self.sub_client.subscribe_price_depth_bbo_event(self.symbols, self.ticker_message)
		except Exception as e:
			print(e)


def get_socket_data(symbol, limit):
	param = {"symbol": symbol, "limit": limit}
	api = HuoBiWsClient(param=param)
	api.get_ticker_socket()


if __name__ == '__main__':
	symbol, limit = "ethusdt", 20
	thread = Thread(target=get_socket_data, args=(symbol, limit)).start()
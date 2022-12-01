import json
import time

from threading import Thread
import json
from qts.utils.exchange.BINANCE.client import Client
from qts.utils.exchange.BINANCE.websockets import BinanceSocketManager


class BinAnWsClient:
    def __init__(self, param,):
        # api_key = 'FeY0y3dP5HKM4b7X95QBa3ysRDmrWj3Fn9jLJKmqqvgob8FTQHXzQtFBjM68h0pL'
        # api_secret = 'SO3AgukQpWfdRAyvFyvIg3cVSksDt4sMcNGP8B8S0AZUxd30i9YHucFpQs7vK2JY'
        self.api_key = ""  # param["api_key"]
        self.api_secret = ""  # param["api_secret"]
        self.symbols = param["symbol"]
        self.limit = param["limit"]
        self.client = Client(api_key=self.api_key, api_secret=self.api_secret)
        self.sub_client = BinanceSocketManager(self.client)

    def depth_message(self, msg):
        # limit: 5/10/20

        from qts import redis_deal
        data = redis_deal.hget('BINANCE', 'depth')
        result = (json.loads(data) if data else {})
        if self.symbols not in result:
            result[self.symbols] = {}

        # result = redis_deal.hmget("BINANCE", ["DEPTH"])
        # DEPTH = (eval(result[0]) if result[0] else {})
        # if self.symbols not in DEPTH:
        #     DEPTH[self.symbols] = {}
        asks_list, bids_list = [], []
        if "asks" in msg:
            asks_info = msg.get("asks")
            for ask in asks_info:
                asks_list.append({'price': float(ask[0]), 'amount': float(ask[1])})
        if "bids" in msg:
            bids_info = msg.get("bids")
            for ask in bids_info:
                bids_list.append({'price': float(ask[0]), 'amount': float(ask[1])})
        depth = {"asks": asks_list, "bids": bids_list, "time": time.time() * 1000}

        # DEPTH[self.symbols].update(depth)
        # redis_deal.hmset("BINANCE", {"DEPTH": DEPTH})
        result[self.symbols].update(depth)
        depth_info = json.dumps(result)
        redis_deal.hset("BINANCE", 'depth', depth_info)

    def symbol_ticker_message(self, msg):
        from qts import redis_deal
        last_price = (msg.get("c") if msg.get("c") else 0)
        buy_price = (msg.get("b") if msg.get("b") else 0)
        sell_price = (msg.get("a") if msg.get("a") else 0)

        data = redis_deal.hget('BINANCE', 'ticker')
        result = (json.loads(data) if data else {})
        if self.symbols not in result:
            result[self.symbols] = {}

        # result = redis_deal.hmget("BINANCE", ["DEPTH"])
        # DEPTH = (eval(result[0]) if result[0] else {})
        # if self.symbols not in DEPTH:
        #     DEPTH[self.symbols] = {}
        ticker = {"last_price": float(last_price), "buy_price": float(buy_price), "sell_price": float(sell_price)}
        if "ticker" not in result[self.symbols]:
            result[self.symbols]["ticker"] = {}
        result[self.symbols]["ticker"].update(ticker)

        # redis_deal.hmset("BINANCE", {"DEPTH": DEPTH})
        ticker_info = json.dumps(result)
        redis_deal.hset("BINANCE", 'ticker', ticker_info)

    def ticker_message(self, ticker_list):
        # print("-ok-", len(ticker_list))
        try:
            from qts import redis_deal
            for msg in ticker_list:
                symbols = (msg.get("s") if msg.get("s") else "")
                last_price = (msg.get("c") if msg.get("c") else 0)
                buy_price = (msg.get("b") if msg.get("b") else 0)
                sell_price = (msg.get("a") if msg.get("a") else 0)

                data = redis_deal.hget('BINANCE', 'ticker')
                print("---ticker_message_data---:", data)
                result = (json.loads(data) if data else {})
                if symbols not in result:
                    result[symbols] = {}

                # result = redis_deal.hmget("BINANCE", ["DEPTH"])
                # DEPTH = (eval(result[0]) if result[0] else {})
                # if symbols not in DEPTH:
                #     DEPTH[symbols] = {}
                ticker = {"last_price": float(last_price), "buy_price": float(buy_price),
                          "sell_price": float(sell_price)}
                if "ticker" not in result[symbols]:
                    result[symbols]["ticker"] = {}
                result[symbols]["ticker"].update(ticker)

                # redis_deal.hmset("BINANCE", {"DEPTH": DEPTH})
                ticker_info = json.dumps(result)
                redis_deal.hset("BINANCE", 'ticker', ticker_info)
        except Exception as e:
            print("ticker_message:", e)

    def kline_message(self, msg):
        print("--kline_message--:", msg)

    def get_ticker_socket(self, ):
        try:
            self.sub_client.start_ticker_socket(self.ticker_message)
            # self.sub_client.start_user_socket(self.trading_list_message)
        except Exception as e:
            print(e)

    def get_depth_socket(self, ):
        try:
            self.sub_client.start_depth_socket(self.symbols, self.depth_message, self.limit)
        except Exception as e:
            print(e)

    def get_kline_socket(self, ):
        try:
            self.sub_client.start_kline_socket(self.symbols, self.kline_message, interval="15m")
        except Exception as e:
            print(e)

    def run(self):
        """开启websocket推送"""
        self.sub_client.start()


def get_socket_data(symbol, limit):
    param = {"symbol": symbol, "limit": limit}
    api = BinAnWsClient(param=param)
    api.get_kline_socket()
    api.run()


if __name__ == '__main__':
    # param = 'symbol=WTC/USDT&limit=100'
    # BinAnWsClient(param=param).start_func_BinAn()
    symbol, limit = "WTCUSDT", 20
    thread = Thread(target=get_socket_data, args=(symbol, limit)).start()
    while 1:
        # print('DEPTH', DEPTH)
        # print('DEPTHCHART', DEPTHCHART)
        time.sleep(5)
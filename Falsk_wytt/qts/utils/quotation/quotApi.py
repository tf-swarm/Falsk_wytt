import logging
from qts import redis_deal
import json


class QuotApi:

    def get_ticker(self, exchange, symbol):
        # res = redis_deal.hmget("{}".format(exchange), ["DEPTH"])
        # ret_info = (eval(res[0]) if res[0] else {})
        data = redis_deal.hget("{}".format(exchange), 'ticker')
        ret_info = (json.loads(data) if data else {})
        try:
            logging.info("---ticker---", ret_info)
            ticker = {}
            if exchange == "BINANCE":
                new_symbol = symbol.replace("/", "")
                result = ret_info[new_symbol]
            elif exchange == "HUOBI":
                new_symbol = symbol.replace("/", "").lower()
                result = ret_info[new_symbol]
            elif exchange == 'Hoo':
                new_symbol = symbol.replace("/", "-")
                result = ret_info[new_symbol]
            elif exchange == 'BITHUMB':
                index = symbol.index("/")
                new_symbol = str(symbol[:index])
                result = ret_info[new_symbol]
            else:
                result = ret_info[symbol]

            if result:
                ticker = result["ticker"]
            return ticker
        except Exception as e:
            logging.error("交易所:{},币对：{}错误：{}".format(exchange, symbol, e))
            return -1

    def get_depth(self, exchange, symbol, limit=20):
        # res = redis_deal.hmget("{}".format(exchange), ["DEPTH"])
        # ret_info = (eval(res[0]) if res[0] else {})

        data = redis_deal.hget("{}".format(exchange), 'depth')
        ret_info = (json.loads(data) if data else {})
        try:
            logging.info("---depth---", ret_info)
            depth_info = {}
            if exchange == "BINANCE":
                new_symbol = symbol.replace("/", "")
                result = ret_info[new_symbol]
            elif exchange == "HUOBI":
                new_symbol = symbol.replace("/", "").lower()
                result = ret_info[new_symbol]
            elif exchange == 'Hoo':
                new_symbol = symbol.replace("/", "-")
                result = ret_info[new_symbol]
            elif exchange == 'BITHUMB':
                index = symbol.index("/")
                new_symbol = str(symbol[:index])
                result = ret_info[new_symbol]
            else:
                result = ret_info[symbol]

            if result:
                asks, bids = result["asks"][limit], result["bids"][limit]
                depth_info.update({"asks": asks, "bids": bids})

            return depth_info
        except Exception as e:
            logging.error("交易所:{},币对：{}错误：{}".format(exchange, symbol, e))
            return -1

    def get_strategy_status(self, strategy_id):
        """策略状态"""
        # 0: 停止策略 1: 启动策略 2: 删除策略
        res = redis_deal.hmget("strategy", ["{}".format(strategy_id)])
        status = (int(res[0]) if res[0] else -1)
        return status

    def del_strategy_id(self, strategy_id):
        """刪除策略"""
        redis_deal.hdel("strategy", "{}".format(strategy_id))


QuotApi = QuotApi()
# print(QuotApi.get_ticker("TAIBI", "WTA/WTC"))

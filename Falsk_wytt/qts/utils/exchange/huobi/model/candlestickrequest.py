from qts.utils.exchange.huobi.constant.result import OutputKey
from qts.utils.exchange.huobi.impl.utils import *
from qts.utils.exchange.huobi.impl.utils.channelparser import ChannelParser
from qts.utils.exchange.huobi.model.constant import *
from qts.utils.exchange.huobi.model.candlestick import Candlestick


class CandlestickRequest:
    """
    The candlestick/kline data received by subscription of candlestick/kline.

    :member
        symbol: the symbol you subscribed.
        timestamp: the UNIX formatted timestamp generated by server in UTC.
        interval: candlestick/kline interval you subscribed.
        data: the data of candlestick/kline.

    """

    def __init__(self):
        self.id = 0
        self.symbol = ""
        self.timestamp = 0
        self.interval = CandlestickInterval.INVALID
        self.data = list()

    @staticmethod
    def json_parse(json_wrapper):
        ch = json_wrapper.get_string(OutputKey.KeyChannelRep)
        parse = ChannelParser(ch)
        candlestick_req = CandlestickRequest()
        candlestick_req.id = json_wrapper.get_int("id")
        candlestick_req.timestamp = candlestick_req.id
        candlestick_req.symbol = parse.symbol
        candlestick_req.interval = ""
        tick = json_wrapper.get_array(OutputKey.KeyData)
        candlestick_list = list()
        for item in tick.get_items():
            data = Candlestick.json_parse(item)
            candlestick_list.append(data)

        candlestick_req.data = candlestick_list
        return candlestick_req

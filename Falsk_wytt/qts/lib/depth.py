
from threading import Thread
from qts.lib.bttv_pymysql import read_data
from qts.utils.exchange.TAIBI.wsClient import TaBiWsClient
from qts.utils.exchange.BINANCE.wsClient import BinAnWsClient
from qts.utils.exchange.huobi.wsClient import HuoBiWsClient
from qts.lib.power import get_exchange_list
from time import sleep


def get_depth(exchange, symbol, limit):
    # 通过websocket获取

    if exchange == 'BINANCE':
        symbol = symbol.replace("/", "")
        limit = limit - 80
        param = {"symbol": symbol, "limit": limit}
    
        # api = BinAnWsClient(param=param)
        # from qts import redis_deal
        # redis_deal.hdel("BINANCE", "DEPTH")
        # api.get_depth_socket()
        # api.get_ticker_socket()
        # api.get_kline_socket()
        # api.run()
    if exchange == 'HUOBI':
        symbol = symbol.replace("/", "").lower()
        limit = 20
        param = {"symbol": symbol, "limit": limit}
        # api = HuoBiWsClient(param=param)
        # api.get_depth_socket()
        # api.get_ticker_socket()

    if exchange == 'BITHUMB':
        pass

    if exchange == 'Hoo':
        pass

    if exchange == 'TAIBI':
        param = "symbol={}&limit={}".format(symbol, limit)
        TaBiWsClient(param=param).start_func_tb()

    # 通过HTTP轮询获取
    # if exchange == 'Came':
    #     while True:
    #         res = ExchangeAPI().get_depth(symbol=symbol)
    #         if res:
    #             DEPTH[exchange] = {}
    #             DEPTH[exchange][symbol] = {}
    #             DEPTH[exchange][symbol]['asks'] = res['sell']
    #             DEPTH[exchange][symbol]['bids'] = res['buy']
    #             DEPTH[exchange][symbol]['time'] = time.time()
    #
    #         sleep(0.3)


def depth_():
    # sql = "select * from t_user"
    # user_list = read_data(sql=sql)
    #
    # for user in user_list:
    #     threading.Thread(target=get_depth, args=(user['exchange'], user['symbol'], 100)).start()

    exchange_list = get_exchange_list()
    for result in exchange_list:
        exchange = result["name"]
        for res_symbol in result["children"]:
            symbol = res_symbol["name"]
            Thread(target=get_depth, args=(exchange, symbol, 100)).start()






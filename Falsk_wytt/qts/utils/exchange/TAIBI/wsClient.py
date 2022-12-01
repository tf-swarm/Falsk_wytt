import json
import time

import websocket
from qts.constants import DEPTH, TICKER, THE_LATEST_DEAL, DEPTHCHART
from qts.utils.exchange.TAIBI.conts import WS_DEPTH_TRADE

CONNECT_STATUS = {'tabi': False}
trade_dict = {'order': []}


class TaBiWsClient:
    def __init__(self, param,):
        self.ws = None
        self.host = WS_DEPTH_TRADE
        self.param = param

    def on_message(self, msg):
        msg = json.loads(msg)
        # print("------on_message------", msg)
        if msg:
            CONNECT_STATUS['tabi'] = True
            if msg.get('1') and msg.get('3'):
                symbol = msg['3']
                # print('长度', len(msg['1']))
                for trade in msg['1']:
                    dict = {}
                    dict['price'] = float(trade['p'])
                    dict['num'] = float(trade['q'])
                    dict['type'] = 'BUY' if trade['s'] == 1 else 'SELL'
                    dict['time'] = trade['t']
                    trade_dict['order'].append(dict)
                    trade_dict['order'].sort(key=lambda x: x['time'], reverse=True)
                    if len(trade_dict['order']) > 20:
                        trade_dict['order'].pop(-1)

                if symbol not in THE_LATEST_DEAL:
                    THE_LATEST_DEAL[symbol] = {}

                THE_LATEST_DEAL[symbol]['lastTrade'] = {'price': msg.get('4'), '$price': msg.get('5'), '¥price': msg.get('6')}
                THE_LATEST_DEAL[symbol]['list'] = trade_dict
                THE_LATEST_DEAL[symbol]['time'] = time.time()

            if msg.get('2') and msg.get('3'):
                # print('深度:', value)
                # print('深度:', len(msg['2']))
                symbol = msg['3']
                asks, bids = [], []
                # for data in msg['2']:
                #     if data['s'] == 1:
                #         b_list = [float(data['p']), float(data['q'])]
                #         bids.append(b_list)
                #     if data['s'] == 2:
                #         a_list = [float(data['p']), float(data['q'])]
                #         asks.append(a_list)
                for temp in msg['2']:
                    if temp['s'] == 2:
                        asks.append({'price': float(temp['p']), 'amount': float(temp['q'])})
                    if temp['s'] == 1:
                        bids.append({'price': float(temp['p']), 'amount': float(temp['q'])})

                last_price = (float(msg['4']) if msg.get('4') else -1)
                buy_price = (bids[0]["price"] if len(bids) > 0 else -1)
                sell_price = (asks[0]["price"] if len(asks) > 0 else -1)

                ticker = {"last_price": last_price, "buy_price": buy_price, "sell_price": sell_price}

                if symbol not in DEPTH:
                    DEPTH[symbol] = {}

                if symbol not in TICKER:
                    TICKER[symbol] = {}

                DEPTH[symbol]['asks'] = asks
                DEPTH[symbol]['bids'] = bids
                TICKER[symbol]['ticker'] = ticker
                DEPTH[symbol]['time'] = time.time() * 1000
                # DEPTH['TAIBI'][symbol]['rate'] = RATE
                # print('深度:DEPTH', id(DEPTH))

                DEPTHCHART[symbol] = {}
                # sell
                ask_volume = 0
                bid_volume = 0
                asks_list = []
                bids_list = []
                for data in msg['2']:
                    if data['s'] == 1:
                        bid_volume += float(data['q'])
                        list = [float(data['p']), bid_volume]
                        bids_list.append(list)
                    if data['s'] == 2:
                        ask_volume += float(data['q'])
                        list = [float(data['p']), ask_volume]
                        asks_list.append(list)

                DEPTHCHART[symbol]['asks'] = asks_list
                DEPTHCHART[symbol]['bids'] = bids_list
                DEPTHCHART[symbol]['time'] = time.time() * 1000

            # print('DEPTH', DEPTH)
            # print('THE_LATEST_DEAL', THE_LATEST_DEAL)
            from qts import redis_deal
            depth_info = json.dumps(DEPTH)
            redis_deal.hset("TAIBI", 'depth', depth_info)
            ticker_info = json.dumps(TICKER)
            redis_deal.hset("TAIBI", 'ticker', ticker_info)
            # TAIBI = {"THE_LATEST_DEAL": THE_LATEST_DEAL, "DEPTH": DEPTH, "DEPTHCHART": DEPTHCHART}
            # redis_deal.hmset("TAIBI", TAIBI)

    def on_error(self, error):
        # print(ws)
        print(error)

    def on_close(self):
        # print(ws)

        CONNECT_STATUS['tabi'] = False

    def on_open(self):
        pass

    def start_func_tb(self, ):
        # 'wss://app.taibi.io/depthWSURL/api/v1/ws/market'
        url = self.host + '?' + self.param
        # print("------------url", url)
        # print("--------CONNECT_STATUS:", CONNECT_STATUS)
        while CONNECT_STATUS['tabi'] == False:
            websocket.enableTrace(True)
            self.ws = websocket.WebSocketApp(url,
                                             on_message=self.on_message,
                                             # on_data=on_data,
                                             on_error=self.on_error,
                                             on_open=self.on_open,
                                             on_close=self.on_close, )
            self.ws.run_forever(ping_interval=60, ping_timeout=5)


# def get_depth_info(symbol):
#     param = 'symbol={}&limit=20'.format(symbol)
#     TaBiWsClient(param=param).start_func_tb()


if __name__ == '__main__':
    param = 'symbol=WTC/USDT&limit=100'
    TaBiWsClient(param=param).start_func_tb()
    # thread = Thread(target=get_depth_info, args=("WTA/WTC",)).start()
    # while 1:
    #     print('DEPTH', DEPTH)
    #     # print('DEPTHCHART', DEPTHCHART)
    #     time.sleep(5)

        # print('THE_LATEST_DEAL', THE_LATEST_DEAL)
# -*- coding: UTF-8 -*-
"""
wta币对深度管理+盘口跳动

author  : keyouzhi
created : 2020-11-23
"""
from qts.utils.quotation.quotApi import QuotApi
from qts.utils.exchange.TAIBI.taibiApi import CTB
import threading,time
import numpy as np

from concurrent import futures
from concurrent.futures.thread import ThreadPoolExecutor
executor_ = ThreadPoolExecutor(max_workers=10)

from qts.utils.util.InitLog import init_log
import logging

logging.getLogger('requests').setLevel(logging.ERROR)
logging.getLogger('connectionpool').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)

Logging = logging.getLogger()

init_log("orderbookV1.0")


class COrderBook(threading.Thread):
    def __init__(self, params):
        threading.Thread.__init__(self)
        self.exchange = params["exchange"]
        self.api_key, self.secret_key = params["api_key"], params["secret_key"]
        self.type = int(params['model_type'])
        self.buy_amount, self.sell_amount = params['buy_amount'], params['sell_amount']
        self.buy_depth, self.sell_depth = params['buy_depth'], params['sell_depth']
        self.bids_spread, self.asks_spread = params['bids_spread'], params['asks_spread']
        self.order_num = int(params['order_num'])
        self.delay = params['delay']
        self.max_waitTime, self.min_waitTime = params['max_waitTime'], params['min_waitTime']

        self.price_precision, self.volume_precision = params['price_precision'], params['volume_precision']

        self.active = True
        # 自由波动模式
        if self.type == 0:
            self.day_rate = params['day_rate']
        # 目标价模式
        elif self.type == 1:
            self.day_rate = params['day_rate']
            self.target_price  = params['target_price']
            self.end_date = params['end_date']
        # 跟市模式
        elif self.type == 2:
            self.order_filter = params['order_filter']
        # 跟随模式
        elif self.type == 3:
            self.flw_exchange_01 = params['flw_exchange_01']
            self.flw_symbol_01 = params['flw_symbol_01']

            self.flw_exchange_02 = params['flw_exchange_02']
            self.flw_symbol_02 = params['flw_symbol_02']


        self.waitTime = self.min_waitTime
        self.askprice = 0.0
        self.bidprice = 0.0
        self.nextprice = 0.0

        self.quot = QuotApi

        #self.lastprice = 0.044428

        if self.exchange == "TAIBI":
            self.api = CTB(self.api_key, self.secret_key)
            self.symbol = params['symbol']
        elif self.exchange == "BINANCE":
            self.api = CBinance(self.api_key, self.secret_key)
            self.symbol = symbol.replace('/', '')
        elif self.exchange == "BITHUMB":
            self.api = CBithumb(self.api_key, self.secret_key)
            self.symbol = symbol.find('/')[0]

        self.lastprice = self.quot.get_ticker(self.exchange, self.symbol)['last_price']



    def get_quot(self):
        ticker = self.quot.get_ticker(self.exchange, self.symbol)
        print('ticker:', ticker)
        return  ticker

    def get_orders(self):

        orders = self.api.get_orders(self.symbol)
        print("--orders", orders)

    def get_externalorders(self):
        """获取外部挂单"""
        try:
            orders = self.api.get_orders(self.symbol)
            depth = self.quot.get_depth(self.exchange, self.symbol)

            for o in orders:
                if o['side'] == 'buy':
                    for dp in depth['bids']:
                        if float(o['price']) == dp['price']:
                            dp['volume'] = dp['volume'] - float(o['volume']) + float(o['trade_volume'])
                            if dp['volume'] < self.order_filter:
                                depth['bids'].remove(dp)
                elif o['side'] == 'sell':
                    for dp in depth['asks']:
                        if float(o['price']) == dp['price']:
                            dp['volume'] = dp['volume'] - float(o['volume']) + float(o['trade_volume'])
                            if dp['volume'] < self.order_filter:
                                depth['asks'].remove(dp)
            return depth
        except Exception as e:
            Logging.exception('exchange:{},symbol:{},get_externalorders 错误:{}'.format(self.exchange, self.symbol, e))
            return None

    def get_price(self):
        """获取t+1时间点基准价格，买一价，卖一价"""
        try:
            # 选择目标价模式
            if self.type == 1:
                rematime = time.mktime(time.strptime(self.end_date, '%Y-%m-%d %H:%M:%S')) - int(time.time())
                if rematime > 0:
                    self.nextprice = (self.target_price - self.lastprice) * self.waitTime / rematime + \
                                     self.lastprice * (1 + np.random.normal(0, self.day_rate * np.sqrt(self.waitTime) / 294))
                else:
                    self.nextprice = self.lastprice * (1 + np.random.normal(0, self.day_rate*np.sqrt(self.waitTime)/294))
            # 选择自由波动模式
            elif self.type == 0:
                self.nextprice = self.lastprice * (1 + np.random.normal(0, self.day_rate*np.sqrt(self.waitTime)/294))
            # 选择跟市模式
            elif self.type == 2:
                depth = self.get_externalorders()
                self.nextprice = (depth['bids'][0]['price'] + depth['asks'][0]['price']) / 2
            elif self.type == 3:
                ticker1 = self.quot.get_ticker(self.flw_exchange_01, self.flw_symbol_01)
                if self.flw_exchange_02 != "":
                    ticker2 = self.quot.get_ticker(self.flw_exchange_02, self.flw_symbol_02)
                    self.nextprice = ticker1['last_price'] * ticker2['last_price']
                else:
                    self.nextprice = ticker1['last_price']

            self.bidprice = round(self.nextprice * (1 - self.bids_spread), self.price_precision)
            self.askprice = round(self.nextprice * (1 + self.asks_spread), self.price_precision)
        except Exception as e:
            Logging.exception('交易所：{},币对:{},获取下一价格错误:{}'.format(self.exchange, self.symbol, e))

    def get_waitTime(self):
        """得到等待休眠时间"""
        self.waitTime = round(np.random.uniform(self.min_waitTime, self.max_waitTime), 2)

    def get_price_thread(self):
        """获取下一次价格线程"""
        def get_nextprice():
            while self.active:
                try:
                    self.get_waitTime()
                    time.sleep(self.waitTime)
                    self.get_price()
                except Exception as e:
                    Logging.exception('交易所：{},币对:{},获取下一价格错误:{}'.format(self.exchange, self.symbol, e))
        thread = threading.Thread(target=get_nextprice)
        thread.daemon = True
        thread.start()

    def batch_buy(self, os:[]):
        """批量下买单"""
        print('buy', os)
        b_os = []
        try:
            if os:
                for i in range(len(os)):
                    buyid = self.api.Buy(self.symbol, os[i][0], os[i][1])
                    b_os.append(buyid)
                    time.sleep(self.delay)
            print('bos:', b_os)
            Logging.info('交易所：{},币对:{},b_os:{}'.format(self.exchange, self.symbol, b_os))
            return  b_os
        except Exception as e:
            Logging.exception('交易所：{},币对:{},批量下买单错误:{}'.format(self.exchange, self.symbol, e))
            return -1

    def batch_sell(self, os: []):
        """批量下买单"""
        print('sell',os)
        s_os = []
        try:
            if os:
                for i in range(len(os)):
                    sellid = self.api.Sell(self.symbol, os[i][0], os[i][1])
                    s_os.append(sellid)
                    time.sleep(self.delay)
            print('sos:', s_os)
            Logging.info('交易所：{},币对:{},s_os:{}'.format(self.exchange, self.symbol, s_os))
            return s_os
        except Exception as e:
            Logging.exception('交易所：{},币对:{},批量下卖单错误:{}'.format(self.exchange, self.symbol, e))
            return -1

    def updata_orderbook(self):
        """铺深度"""
        try:
            if self.bidprice > 0.0 and self.askprice > 0.0:
                buypricelist = np.round(np.random.uniform(self.bidprice * (1-self.buy_depth), self.bidprice, self.order_num), self.price_precision)
                sellpricelist = np.round(np.random.uniform(self.askprice , self.askprice * (1+self.sell_depth), self.order_num), self.price_precision)

                buyamountlist = np.round(np.random.uniform(self.buy_amount[0], self.buy_amount[1], self.order_num), self.volume_precision)
                sellamountlist = np.round(np.random.uniform(self.sell_amount[0], self.sell_amount[1], self.order_num), self.volume_precision)

                f = executor_.submit(self.batch_buy, list(zip(buypricelist,buyamountlist)))
                f1 = executor_.submit(self.batch_sell, list(zip(sellpricelist,sellamountlist)))
                futures.wait([f,f1], timeout=80)
                if not f.done():
                    Logging.error('任务f{}超时'.format(f))
                    f.cancel()
                if not f1.done():
                    Logging.error('任务f1{}超时'.format(f1))
                    f1.cancel()

        except Exception as e:
            Logging.exception('交易所：{},币对:{},铺深度错误:{}'.format(self.exchange, self.symbol, e))

    def cancelorders_timeout_thread(self):
        """轮询撤单线程"""
        def cancelorders_timeout():
            while self.active:
                print("----cancelorders_timeout--end")
                self.api.cancel_orders_timeout(self.symbol, 20)
                time.sleep(2)
        thread = threading.Thread(target=cancelorders_timeout)
        thread.daemon = True
        thread.start()


    def set_active(self):
        self.active = False
        print("----set_active", self.active)


    def run(self):
        self.get_price_thread()
        self.cancelorders_timeout_thread()
        while self.active:
            try:
                print(self.nextprice,self.askprice,self.bidprice)
                self.updata_orderbook()
                time.sleep(1)

            except Exception as e:
                print(e)
                time.sleep(5)
        # 当停止策略的时候撤销所有订单
        if not self.active:
            print("---exit--cancel_all_orders")
            self.api.cancel_all_orders(self.symbol)
                



if __name__ == '__main__':
    # params = {'exchange': 'TAIBI', 'symbol': 'WTA/WTC', 'model_type': '1', 'buy_amount': [1.0, 2.0], 'sell_amount': [1.0, 3.0], 'buy_depth': 0.15, 'sell_depth': 0.15, 'bids_spread': 0.002, 'asks_spread': 0.002, 'order_num': 10, 'delay': 0.6, 'max_time': 32, 'min_time': 4, 'day_rate': 0.05, 'api_key': 'bb2e2e9d2630dabedb0ea1e4366c9d67', 'secret_key': '6fe7bd45c68dad0f775b65b15c7b28ef'}
    # obj  = COrderBook(params)
    # obj.start()
    pass
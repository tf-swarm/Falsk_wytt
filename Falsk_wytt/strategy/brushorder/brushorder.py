# -*- coding: UTF-8 -*-
"""
wta币对深度管理+盘口跳动

author  : keyouzhi
created : 2020-11-24
"""

from qts.utils.quotation.quotApi import QuotApi
from qts.utils.exchange.TAIBI.taibiApi import CTB
from qts.utils.exchange.BINANCE.binanceApi import CBinance
from qts.utils.exchange.BITHUMB.bithumbApi import CBithumb
import threading,time
import numpy as np
import random

from qts.utils.util.InitLog import init_log

import logging

logging.getLogger('requests').setLevel(logging.ERROR)
logging.getLogger('connectionpool').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)

Logging = logging.getLogger()


class CBrushOrder(threading.Thread):
    def __init__(self, params):
        threading.Thread.__init__(self)
        self.strategy_id = params['strategy_id']
        self.exchange = params['exchange']
        self.api_key, self.secret_key = params["api_key"], params["secret_key"]
        self.quoteBuffer = params['quote_buffer']
        self.max_waitTime, self.min_waitTime = params['max_waitTime'], params['min_waitTime']
        self.day_rate = params['day_rate']
        self.amount, self.baseAmount = params['amount'], params['base_amount']

        self.price_precision, self.volume_precision = params['price_precision'], params['volume_precision']

        self.quot = QuotApi
        if self.exchange == "TAIBI":
            self.api = CTB(self.api_key, self.secret_key)
            self.symbol = params['symbol']
        elif self.exchange == "BINANCE":
            print("---BINANCE---", self.api_key, self.secret_key)
            self.api = CBinance(self.api_key, self.secret_key)
            symbol = params['symbol']
            self.symbol = symbol.replace('/', '')
        elif self.exchange == "BITHUMB":
            self.api = CBithumb(self.api_key, self.secret_key)
            symbol = params['symbol']
            self.symbol = symbol[:symbol.find('/')]

        self.waitTime = self.min_waitTime
        self.side = 1

        self.active = True

        self.best_quote = self.quot.get_ticker(self.exchange, self.symbol)

    def get_waitTime(self):
        """得到等待休眠时间"""
        self.waitTime = round(np.random.uniform(self.min_waitTime, self.max_waitTime), 2)

    def get_amount(self):
        """生产刷单数量"""
        try:
            amount = self.baseAmount * (0.1 + np.random.poisson(0.8)) * (1 + np.random.normal(0, 0.4))

            if amount < self.amount[0]:
                amount = np.random.uniform(self.amount[0], self.amount[0] * 1.05)
            elif amount > self.amount[1]:
                amount = np.random.uniform(self.amount[1] * 0.95, self.amount[1])
            return round(amount, self.volume_precision)
        except Exception as e:
            Logging.exception('exchange:{},symbol:{},get_amount 错误:{}'.format(self.exchange, self.symbol, e))
            return self.amount[0]



    def get_price(self):
        """生产刷单价格"""
        try:
            self.best_quote = self.quot.get_ticker(self.exchange, self.symbol)
            if self.best_quote['sell_price'] - self.best_quote['buy_price'] <= 2 * self.quoteBuffer:
                Logging.info('symbol:{}盘口价差太小，不刷单'.format(self.symbol))
                return -1
            price = self.best_quote['last_price'] * (1 + np.random.normal(0, self.day_rate * np.sqrt(self.waitTime) / 294))

            if price < self.best_quote['buy_price'] + self.quoteBuffer:
                price = self.best_quote['buy_price'] + self.quoteBuffer
            elif price > self.best_quote['sell_price'] - self.quoteBuffer:
                price = self.best_quote['sell_price'] - self.quoteBuffer

            if price > self.best_quote['last_price']:
                self.side = 1
            elif price < self.best_quote['last_price']:
                self.side = 2
            else:
                self.side = int(random.uniform(1, 3))

            # self.best_quote['last_price'] = price
            return round(price, self.price_precision)

        except Exception as e:
            Logging.exception('交易所:{},币对:{},get_price 错误:{}'.format(self.exchange, self.symbol, e))
            return -1

    def set_active(self):
        print("-----self.active1111", self.active)
        self.active = False
        print("-----self.active222", self.active)

    def make_vol(self):
        """对敲"""
        try:
            self.get_waitTime()
            time.sleep(self.waitTime)
            amount = self.get_amount()
            price = self.get_price()

            Logging.info("exchange:{},symbol:{},price:{},amount:{},side:{},waitTime:{}".format(self.exchange, self.symbol, price,
                                                                                      amount, self.side, self.waitTime))
            if price > 0 and amount > 0 and self.best_quote['buy_price'] > 0 and self.best_quote['sell_price'] > 0:
                if self.exchange == 'TAIBI':
                    res = self.api.make_vol(self.symbol, price, amount, self.side)
                else:
                    buyid = ''
                    sellid = ''
                    if self.side ==1:
                        sellid = self.api.Sell(self.symbol, price, amount)
                        buyid = self.api.Buy(self.symbol, price, amount)
                    elif self.side == 2:
                        buyid = self.api.Buy(self.symbol, price, amount)
                        sellid = self.api.Sell(self.symbol, price, amount)
                    self.api.cancel_order(buyid, self.symbol)
                    self.api.cancel_order(sellid, self.symbol)
        except Exception as e:
            Logging.exception('run报错：{}'.format(str(e)))
            return -1

    def run(self):
        while 1:
            active = self.quot.get_strategy_status(self.strategy_id)
            if active == 1:
                self.make_vol()
            elif active == 0:
                break
            elif active == 2:
                self.quot.del_strategy_id(self.strategy_id)
                break
            time.sleep(1)
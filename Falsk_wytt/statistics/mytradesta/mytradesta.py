# -*- coding: UTF-8 -*-
"""
成交历史统计

author  : keyouzhi
created : 2021-04-8
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
# from qts.utils.exchange.BITHUMB.bithumbApi import CBithumb

from qts.utils.util.InitLog import init_log
from qts.utils.util.DataUtility import *

import logging

logging.getLogger('requests').setLevel(logging.ERROR)
logging.getLogger('connectionpool').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)

Logging = logging.getLogger()

init_log("MyTradeV1.0")


class MyTradeSta(threading.Thread):
    """docstring for MyTradeSta"""

    def __init__(self, params):
        super(MyTradeSta, self).__init__()

        self.delay = 43200  # 12小时

        self.exchange = params['exchange']
        self.akey = params['api_key']
        self.skey = params['secret_key']
        self.startTime = params['start_date']
        self.endTime = params['end_date']
        symbol = params['symbol']

        if self.exchange == "BINANCE":
            self.api = CBinance(self.akey, self.skey)
            self.symbol = symbol.replace('/', '')
        # if self.exchange == "huobi":
        #     self.api = CHuobi(self.akey, self.skey)
        #     self.symbol = symbol.replace('/', '').lower()

    def get_mytrades(self):

        mystadesta = {"buy_num": 0.0, "buy_money": 0.0, "buy_average": 0.0, "sell_num": 0.0, "sell_money": 0.0, "sell_average": 0.0}
        try:
            startTime = self.startTime * 1000 - 1
            endTime = self.endTime * 1000
            mytrades = []

            timeArr = np.arange(startTime, endTime, self.delay * 1000)

            if timeArr[-1] != endTime:
                timeArr = np.append(timeArr, endTime)

            for i in range(len(timeArr) - 1):
                trades = self.api.get_trades(self.symbol, timeArr[i] + 1, timeArr[i + 1])

                mytrades = mytrades + trades

            df = pd.DataFrame(mytrades)
            # df.to_csv('wtcusdt.csv')

            if len(df) == 0:
                return mystadesta

            buytrades = df[(df['isBuyer'] == True)]
            selltrades = df[(df['isBuyer'] == False)]
            # buytrades.to_csv('buy.csv')
            # selltrades.to_csv('sell.csv')

            buyamount = sum(buytrades['qty'].values.astype(float))
            buyquote = sum(buytrades['quoteQty'].values.astype(float))

            sellamount = sum(selltrades['qty'].values.astype(float))
            sellquote = sum(selltrades['quoteQty'].values.astype(float))

            mystadesta['buy_num'] = int(buyamount)
            mystadesta['buy_money'] = int(buyquote)
            mystadesta['buy_average'] = round(buyquote / buyamount, 4)

            mystadesta['sell_num'] = int(sellamount)
            mystadesta['sell_money'] = int(sellquote)
            mystadesta['sell_average'] = round(sellquote / sellamount, 4)

            print("买入数量：", int(buyamount), "买入金额:", int(buyquote), "买入均价：", round(buyquote / buyamount, 4))
            print("卖出数量：", int(sellamount), "卖出金额:", int(sellquote), "卖出均价：", round(sellquote / sellamount, 4))
            return mystadesta

        except Exception as e:
            print(e)
            return e


if __name__ == '__main__':
    params = {"exchange": 'BINANCE', 'symbol': 'WTC/USDT',
              'akey': 'FeY0y3dP5HKM4b7X95QBa3ysRDmrWj3Fn9jLJKmqqvgob8FTQHXzQtFBjM68h0pL',
              'skey': 'SO3AgukQpWfdRAyvFyvIg3cVSksDt4sMcNGP8B8S0AZUxd30i9YHucFpQs7vK2JY', 'startTime': 1615219200,
              'endTime': 1617897601}
    # params = {'exchange': 'BINANCE', 'symbol': 'BTC/USDT', 'start_date': 1615248000, 'end_date': 1618012799,
    #  'api_key': 'FeY0y3dP5HKM4b7X95QBa3ysRDmrWj3Fn9jLJKmqqvgob8FTQHXzQtFBjM68h0pL',
    #  'secret_key': 'SO3AgukQpWfdRAyvFyvIg3cVSksDt4sMcNGP8B8S0AZUxd30i9YHucFpQs7vK2JY'}

    mytrade = MyTradeSta(params)


    print(mytrade.get_mytrades())
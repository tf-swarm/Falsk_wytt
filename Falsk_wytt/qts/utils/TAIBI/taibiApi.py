# -*- coding: UTF-8 -*-
"""
taibi api

author  : keyouzhi
created : 2020-06-02
"""
import hmac
import time
import hashlib
import requests
from urllib.parse import quote_plus
from pprint import pprint as pp
import urllib
import urllib.parse
import urllib.request
import yaml
import datetime
import base64
import json
import random
from websocket import create_connection
import threading

import ssl

import sys
import yaml
import os
from os.path import dirname

# ssl._create_default_https_context = ssl._create_unverified_context


class CTB(object):
    """docstring for ClassName"""

    def __init__(self, akey='', skey=''):
        super(CTB, self).__init__()
        self.akey = akey
        self.skey = skey

        self.base_url = 'https://app.taibi.io'
        # self.url = 'http://10.0.197.163:8099'
        # self.url = 'https://app.taibi.io/open_api'
        self.url = 'https://openapi.taibi.io/open_api'

        # self.url = 'http://ec2-18-140-57-24.ap-southeast-1.compute.amazonaws.com:8099'
        #         # 数据的接口
        # self.base_url = 'http://ec2-18-140-57-24.ap-southeast-1.compute.amazonaws.com:8182'

    def __get_sign(self, param):
        '''
        get 签名
        '''
        try:
            newStr = param + self.skey
            sha256 = hashlib.sha256()
            sha256.update(bytes(newStr, encoding='utf-8'))
            res = sha256.digest()

            signature = base64.b64encode(res)
            return signature.decode()

        except Exception as e:
            print(e)
            return -1

    def __post_sign(self, pParams):
        '''
        post方法签名
        '''
        try:
            base64Str = base64.b64encode(bytes(pParams, encoding='utf-8'))
            base64Str = base64Str.decode()
            newStr = base64Str + self.skey
            sha256 = hashlib.sha256()
            sha256.update(bytes(newStr, encoding='utf-8'))
            res = sha256.digest()
            signature = base64.b64encode(res)
            return signature.decode(), base64Str
        except Exception as e:
            print(e)
            return -1

    def http_request(self, method_type, url, params, data=None, add_to_headers=None):
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
            "Accept": "application/json",
        }
        if add_to_headers:
            headers.update(add_to_headers)
        # if method_type == 'POST':
        #   body = urllib.parse.urlencode(data)
        #   data = json.dumps(body)
        # print(method_type, url, params, data)
        try:

            response = requests.request(method_type, url=url, params=params, data=data, headers=headers, timeout=50)

            if response.status_code == 200:
                return response.json()
            else:
                print(response.text)
                return
        except Exception as e:
            print("%s , %s" % (url, e))
            return

    def __http_get_request(self, url, params):
        return self.http_request('GET', url, params)

    def __http_post_request(self, url, params, data):
        return self.http_request('POST', url, params, data)

    def get_depth(self, symbol, limit=100):
        '''
        等到深度
        param 币对 档位数
        '''
        url = self.base_url + '/depthWSURL/api/v1/query/market/depth'

        params = {'symbol': symbol,
                  'limit': limit}
        try:
            depth = self.__http_get_request(url, params)
            return depth
        except Exception as e:
            print(e)
            return -1

    def get_ticker(self, symbol):
        '''
        得到ticker数据
        param symbol
        return {买一价 卖一家 最后成交价}
        '''
        url = self.base_url + '/depthWSURL/api/v1/query/market/depth'

        params = {'symbol': symbol,
                  'limit': 1}
        try:
            tickers = self.__http_get_request(url, params)
            # print(tickers)
            ticker = {'buyprice': -1, "sellprice": -1, "lastprice": -1}
            if tickers['bids'] != []:
                ticker['buyprice'] = float(tickers['bids'][0]['price'])
            if tickers['asks'] != []:
                ticker['sellprice'] = float(tickers['asks'][0]['price'])
            ticker['lastprice'] = float(tickers['new_trade_price'])
            # print(ticker)
            return ticker
        except Exception as e:
            print(e)
            return -1

    def get_trade_records(self):
        try:
            nowtime = int(time.time())
            # param = {'symbol':"WTA/WTC",'ts': nowtime,"type":1,"page":0,"size":10}

            param = {'page': 0, 'size': 10, 'symbol': 'WTA/WTC', 'ts': nowtime, 'type': 1}
            params = urllib.parse.urlencode(param).replace('%2F', '/')

            sign = self.__get_sign(params)
            # sendParams = {'access_key': self.akey, 'sign': sign, 'symbol':"WTA/WTC",'ts': nowtime,"type":1,"page":0,"size":10 }
            sendParams = {'access_key': self.akey, 'type': 1, 'sign': sign, 'ts': nowtime, 'symbol': 'WTA/WTC',
                          'page': 0, 'size': 10}
            postdata = urllib.parse.urlencode(sendParams)

            request_path = self.url + '/api/v1/query/trade/records?' + postdata

            res = requests.get(request_path)

            if res.status_code == 200:
                # print(res.json()['data'])
                return res.json()['data']
            else:
                print(res.status_code)
                return -1

        except Exception as e:
            print('ee', e)
            return -1

    def get_klines(self, symbol, period='15min', count=1):
        '''
        获取K线信息
        param: symbol period
        '''
        try:
            nowtime = int(time.time())
            orders = {'limit': count, 'period': period, 'symbol': symbol, 'ts': nowtime}
            orders = urllib.parse.urlencode(orders).replace('%2F', '/')
            sign = self.__get_sign(orders)
            sendParams = {'access_key': self.akey, 'type': 1, 'sign': sign, 'ts': nowtime, 'symbol': symbol,
                          'limit': count, 'period': period}
            postdata = urllib.parse.urlencode(sendParams)
            request_path = self.url + '/api/v1/query/kline/period?' + postdata
            # print(request_path)
            res = requests.get(request_path)
            if res.status_code == 200:
                return res.json()['data']
            else:
                print(res.status_code)
                return -1

        except Exception as e:
            print(e)
            return -1

    def get_account(self):
        '''
        获取资产余额
        '''
        try:
            nowtime = int(time.time())
            params = {'ts': nowtime}
            params = urllib.parse.urlencode(params)
            sign = self.__get_sign(params)
            sendparams = {'access_key': self.akey, 'sign': sign, 'ts': nowtime}
            #ts=1606714926&access_key=bb2e2e9d2630dabedb0ea1e4366c9d67&sign=SKiicXSx8GTgpz4xwSqSXVJHRflLzl6qcZ7YSyuTYVo%3D
            postdata = urllib.parse.urlencode(sendparams)

            request_path = self.url + '/api/v1/query/user/balance?' + postdata

            acc = requests.get(request_path)

            if acc.status_code == 200:
                accs = acc.json()['data']
                print("----accs-----", accs)
                accs = filter(lambda x: float(x['qty']) + float(x['freeze_qty']), accs)
                # accs = [acc for acc in accs if float(acc['qty']) + float(acc['freeze_qty']) > 0 ]
                balances = []
                for acc in list(accs):
                    balance = {}
                    balance['asset'] = acc['symbol'].upper()
                    balance['free'] = float(acc['qty'])
                    balance['locked'] = float(acc['freeze_qty'])
                    balances.append(balance)

                return balances
            else:
                print(acc.status_code, acc.json())
                return -1
        except Exception as e:
            print(e)
            return -1

    def Buy(self, symbol, price, amount):
        '''
        下买单
        param 币对 价格 数量
        return 订单号
        '''
        # print('buy', symbol, price, amount)
        try:
            orders = {'symbol': symbol, 'side': 1, 'ts': int(time.time()), 'orders': [{'qty': amount, 'price': price}]}
            sign, paramStr = self.__post_sign(json.dumps(orders))
            sendparams = json.dumps({'access_key': self.akey, 'data': paramStr, 'sign': sign})
            request_path = self.url + '/api/v1/order/batch/create'

            res = requests.post(request_path, data=sendparams)
            if res.status_code == 200:
                return res.json()['data'][0]
            else:
                print(res.status_code, res.json())
                return -1
        except Exception as e:
            print(e)
            return -1

    def Sell(self, symbol, price, amount):
        '''
        下卖单
        param 币对 价格 数量
        return id
        '''
        # print('sell', symbol, price, amount)
        try:
            orders = {'symbol': symbol, 'side': 2, 'ts': int(time.time()), 'orders': [{'qty': amount, 'price': price}]}
            sign, paramStr = self.__post_sign(json.dumps(orders))
            sendparams = json.dumps({'access_key': self.akey, 'data': paramStr, 'sign': sign})
            request_path = self.url + '/api/v1/order/batch/create'

            res = requests.post(request_path, data=sendparams)
            if res.status_code == 200:
                return res.json()['data'][0]
            else:
                print(res.status_code, res.json())
                return -1
        except Exception as e:
            print(e)
            return -1

    def cancel_order(self, orderid):
        '''
        取消订单
        param orderid
        '''
        try:
            orders = {'ids': [orderid], 'ts': int(time.time())}
            sign, paramStr = self.__post_sign(json.dumps(orders))
            sendParams = json.dumps({'access_key': self.akey, 'data': paramStr, 'sign': sign})
            request_path = self.url + '/api/v1/order/batch/cancel'

            res = requests.post(request_path, data=sendParams)

            if res.status_code == 200:
                return res.json()
            else:
                print(res.status_code, res.json())
                return -1
        except Exception as e:
            print(e)
            return -1

    def cancel_orders(self, os: []):
        '''
        批量取消订单
        param os列表
        '''
        try:
            if os == []:
                return -1
            orders = {'ids': os, 'ts': int(time.time())}
            sign, paramStr = self.__post_sign(json.dumps(orders))
            sendParams = json.dumps({'access_key': self.akey, 'data': paramStr, 'sign': sign})
            request_path = self.url + '/api/v1/order/batch/cancel'

            res = requests.post(request_path, data=sendParams)

            if res.status_code == 200:
                return res.json()
            else:
                print(res.status_code, res.json())
                return -1
        except Exception as e:
            print(e)
            return -1

    def cancel_orders_timeout(self, symbol, stime=30):
        '''
        轮巡撤单
        param stime 撤单时间间隔
        '''
        try:
            orders = self.get_orders(symbol)

            if len(orders) > 0:
                random.shuffle(orders)
                os = []
                for o in orders:
                    create_timestring = o['created_at'][:19]
                    create_timestamp = time.mktime(time.strptime(create_timestring, '%Y-%m-%dT%H:%M:%S'))
                    nowtime = int(time.time())
                    if nowtime - create_timestamp >= stime:
                        os.append(o['entrust_id'])
                self.cancel_orders(os)
        except Exception as e:
            print('撤单错误：{}'.format(e))

    def get_order(self, orderId, symbol=''):
        '''
        获取订单详情
        '''
        try:
            params = {
                'order_id': orderId,
                'ts': int(time.time())
            }
            strParams = urllib.parse.urlencode(params)
            params['sign'] = self.__get_sign(strParams)
            params['access_key'] = self.akey
            strParams = urllib.parse.urlencode(params)

            url = self.url + '/api/v1/query/order/info?' + strParams

            res = requests.get(url)

            data = res.json()['data']
            # print(data)
            orderinfo = {}
            orderinfo['order_id'] = orderId
            orderinfo['side'] = data['opt']
            orderinfo['price'] = float(data['limit_price'])
            # orderinfo['avg_price'] = float(data['average_price'])
            orderinfo['volume'] = float(data['num'])
            orderinfo['trade_volume'] = float(data['traded_num'])
            orderinfo['timestamp'] = data['created_at']

            return orderinfo
        except Exception as e:
            print(e)
            return -1

    def get_orders(self, symbol):
        '''
        获取当前币对所有未成交订单
        '''
        try:
            nowtime = int(time.time())
            orders = {'symbol': symbol, 'ts': nowtime, 'type': 1}
            orders = urllib.parse.urlencode(orders).replace('%2F', '/')
            sign = self.__get_sign(orders)
            sendParams = {'access_key': self.akey, 'type': 1, 'sign': sign, 'ts': nowtime, 'symbol': symbol}
            postdata = urllib.parse.urlencode(sendParams)
            request_path = self.url + '/api/v1/query/order/list?' + postdata
            orders = requests.get(request_path)

            if orders.status_code == 200:
                return orders.json()['data']
            else:
                print(orders.status_code, orders.json())
                return -1

        except Exception as e:
            print(e)
            return -1

    def get_orderids(self, symbol):
        oids = []
        os = self.get_orders(symbol)

        for o in os:
            oids.append(o['entrust_id'])
        return oids

    def make_vol(self, symbol, price, amount, side):
        '''
        刷成交量 不进撮合
        '''
        try:
            orderinfo = {
                'qty': str(amount),
                'price': str(price),
                'side': side,
                'market': symbol,
                'time': int(time.time())
            }

            sendParams = json.dumps([orderinfo])
            request_path = self.url + '/api/v1/market/make/vol'
            res = requests.post(request_path, data=sendParams)
            if res.status_code == 200:
                return res.json()
            else:
                print(res.status_code, res.json())
                return -1

        except Exception as e:
            raise

    def get_userfin(self, coin, limit=1000, page=1, user_name=None):
        headers = {
            'Content-Type': 'application/json',
            'accesstoken': 'r23eiwtueiprwtg23896jhj14ktekt',
        }

        url = 'https://app.taibi.io/open_api/api/user/get_userfin'
        body = {'coin_name': coin,
                'limit': limit,
                'page': page}

        try:
            if user_name:
                body['user_name'] = str(user_name)

            response = requests.post(url, data=json.dumps(body), headers=headers)
            if response.status_code == 200:
                # print(response.json())
                return response.json()['data']['userfin']

        except Exception as e:
            print('e')
            return -1

    # websocket api
    def sub_taibi_ws(self, symbol, callback):
        while 1:
            try:
                newSymbol = symbol.upper().replace('/', '%2F')

                ws = create_connection(
                    'wss://app.taibi.io/depthWSURL/api/v1/ws/market?symbol=' + newSymbol + '&limit=100')
                while 1:
                    compressData = ws.recv()
                    data = json.loads(compressData)

                    callback(data)

            except Exception as e:
                print(e)
                Logging.error("sub_taibi_ws错误:{}".format(e))
                time.sleep(15)

    def get_taibi_ws(self, symbol, callback):

        thread = threading.Thread(target=self.sub_taibi_ws, args=(symbol, callback))
        thread.daemon = True
        thread.start()

    # def get_taibi_callback(self,data):
    #     print(data)

    # def get_taibi_callback(self, data):
    #     try:
    #         if data.get('3'):
    #             if data['3'] == 'WTA/WTC':
    #                 if data.get('2'):
    #                     asks = []
    #                     bids = []
    #                     for temp in data['2']:
    #                         if temp['s'] == 2:
    #                             asks.append([float(temp['p']), float(temp['q'])])
    #                         elif temp['s'] == 1:
    #                             bids.append([float(temp['p']), float(temp['q'])])
    #                     depth = {'bids':bids, 'asks':asks}

    #                     orders = self.get_orders('WTA/WTC')

    #                     for o in orders:
    #                         if o['opt'] == 1:
    #                             for i in range(len(depth['bids'])):
    #                                 if float(o['limit_price']) == depth['bids'][i][0]:
    #                                     vol = depth['bids'][i][1] - float(o['num']) + float(o['traded_num'])

    #                                     depth['bids'][i].append(vol)
    #                                     depth['bids'][i].append(float(o['num']) - float(o['traded_num']))
    #                         elif o['opt'] == 2:
    #                             for i in range(len(depth['asks'])):
    #                                 if float(o['limit_price']) == depth['asks'][i][0]:
    #                                     vol = depth['asks'][i][1] - float(o['num']) + float(o['traded_num'])

    #                                     depth['asks'][i].append(vol)
    #                                     depth['asks'][i].append(float(o['num']) - float(o['traded_num']))

    #                     for b in range(len(depth['bids'])):
    #                         if len(depth['bids'][b]) == 2:
    #                             depth['bids'][b].append(depth['bids'][b][1])
    #                             depth['bids'][b].append(0)

    #                     # for a in depth['asks']:
    #                     #     if len[a] == 2:
    #                     #         a[2] = a[1]
    #                     #         a[3] = 0

    #                     print(depth['bids'])
    #                     sys.exit()

    #     except Exception as e:
    #         print(e)


if __name__ == "__main__":
    import pandas as pd
    import numpy as np
    # bb2e2e9d2630dabedb0ea1e4366c9d67
    # 自己测试账号
    akey = 'bb2e2e9d2630dabedb0ea1e4366c9d67'
    skey = '6fe7bd45c68dad0f775b65b15c7b28ef'

    # 高账号
    # akey = '19e10848b1df9b4036e7e6519f2f9adb'
    # skey = 'd5abe2cab4d36d84d76b993b2f066370'

    # akey = '122bd3dda9b1700035a4d9f706a3c903'
    # skey = 'e5381d1a0607d0f6e88968592825577d'

    tb = CTB(akey, skey)

    # depth = tb.get_depth('WTA/WTC')
    # print(depth)
    # print(len(depth['asks']),len(depth['bids']))

    # ticker = tb.get_ticker('WTA/WTC')
    # print(ticker)

    # klines = tb.get_klines('WTA/WTC', '1hour', 5)
    # print(klines)
    # close = pd.DataFrame(klines)['close'].values.astype(float)
    # print(close,len(close))

    # stime = time.time()
    # acc = tb.get_account()
    # print(acc)
    # print(time.time() - stime)

    # print(tb.get_ticker('WTA/WTC'))

    # print(tb.get_trade_records())

    #
    # accinfo = tb.get_userfin('wta')
    # print(accinfo)
    # print(accinfo['data']['userfin'])

    # accs = accinfo['data']['userfin']
    # print(len(accs))
    # acc = list(filter(lambda x: float(x['use_amount']) + float(x['freeze_amount']) >= 200 and x['uid'] not in [300143110984384512],accinfo))
    # print(acc)

    # Data = pd.DataFrame(acc)
    # print(sum(Data['use_amount']))
    # Data.to_csv('acc.csv')
    # tb.cancel_orders_timeout('WTA/WTC')

    # stime = time.time()
    # buyid = tb.Sell('WTA/WTC',  0.063215, 1)
    # print(buyid)
    # print(time.time() - stime)

    # os = tb.get_orders('WTA/WTC')
    # print(len(os))
    # buyid = tb.Buy('WTA/WTC',  0.024, 1)
    # print(buyid)
    # tb.cancel_order(1319284241808240640)

    # print(tb.get_order(buyid))
    # res = tb.cancel_orders(os)
    # print(res)

    # stime = time.time()
    os = tb.get_orderids('WTA/WTC')
    print(len(os), os)
    # print(time.time() - stime)
    tb.cancel_orders(os)
    # while 1:
    #     os = tb.get_orderids('WTA/WTC')
    #     print(len(os))
    #     res = tb.cancel_orders(os[:80])

    # stime = time.time()
    # os = tb.get_orders('WTA/WTC')
    # print(time.time() - stime)
    # print(os,len(os))

    # res = tb.get_klines('WTA/WTC','15min',10)

    # print(res)

    # print(tb.get_trade_records())

    # res = tb.matched_order('WTA/WTC', 0.0981, 1, 1)
    # print(res)

    # tb.get_taibi_ws('WTA/WTC', tb.get_taibi_callback)

    # while 1:
    #     time.sleep(2)

#
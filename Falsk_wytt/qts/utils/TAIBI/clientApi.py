import base64
import hashlib
import json
import logging
import time
import urllib.parse

import requests
import urllib3

from qts.utils.TAIBI.conts import BASEURL, HTTP_GET_BALANCE, HTTP_BATCH_CREATE, HTTP_QUERY_ORDER_LIST, \
    HTTP_BATCH_CANCEL_ORDER, \
    HTTP_TEST_DEPTH, HTTP_KLINE, HTTP_QUERY_ORDER_LIST_STATUE, HTTP_GET_ORDER_INFO, HTTP_DEAL_RECORD, \
    HTTP_RECHARGE_RECORD, HTTP_WITHDRAW_DEPOSIT_RECORD, HTTP_HOLD_CURRENCY, HTTP_DEAL_RECORD_ALL, HTTP_DEPTHDETAIL


class TaBiApi:
    def __init__(self, key=None, secret=None, accountID=None):
        self.apiKey = key
        self.secretKey = secret
        self.accountID = accountID
        self.url = BASEURL

    def _request(self, url, data, method):
        urllib3.disable_warnings()
        requests.adapters.DEFAULT_RETRIES = 5
        s = requests.session()
        # 忽略ssl验证
        # s.verify =False
        # 设置连接活跃状态为False
        s.keep_alive = False

        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.71 Safari/537.36',
        }
        try:
            if method == 'post':
                req = s.post(url, data=data, headers=headers, timeout=60, verify=False)

            else:
                req = s.get(url, params=data, headers=headers, timeout=60, verify=False)
            # print(req.url,req.text)
        except Exception as e:
            logging.error("%s:%s \n" % (e, url))
            return None
        if req.status_code != 200:
            if req.text[21:36] == '502 Bad Gateway':
                logging.error('502 Bad Gateway:<!-- a padding to disable MSIE and Chrome friendly error page -->  %s' % url)
            else:
                logging.error("%s:%s \n" % (req.text, url))
            return None

        # 关闭请求  释放内存
        req.close()
        return json.loads(req.text)

    def create_sign(self, param):
        """用于get请求
        :param param:
        :return:
        """
        if self.apiKey is None or self.secretKey is None:
            raise ValueError('apiKey或secretKey不能为空')
        string = ''
        if param:
            params = sorted(param.items(), key=lambda x: x[0])
            for i in params:
                string += str(i[0]) + '=' + str(i[1]) + '&'
        # print(string[:-1])
        newStr = string[:-1] + self.secretKey
        sha256 = hashlib.sha256()
        sha256.update(bytes(newStr, encoding='utf-8'))
        res = sha256.digest()
        signature = base64.b64encode(res)
        return signature.decode()

    def make_sign(self, pParams):
        """
        用于post请求
        获得签名和参数base64字符串
        :param pParams:
        :return:
        """
        if self.apiKey is None or self.secretKey is None:
            raise ValueError('apiKey或secretKey不能为空')

        base64Str = base64.b64encode(bytes(pParams, encoding='utf-8'))
        base64Str = base64Str.decode()
        newStr = base64Str + self.secretKey
        sha256 = hashlib.sha256()
        sha256.update(bytes(newStr, encoding='utf-8'))
        res = sha256.digest()
        signature = base64.b64encode(res)
        return signature.decode(), base64Str

    def get_balance(self):
        param = {
            'ts': int(time.time())
        }
        sign = self.create_sign(param=param)
        param['access_key'] = self.apiKey
        param['sign'] = sign
        url = self.url + HTTP_GET_BALANCE
        return self._request(url=url, data=param, method='get')

    def batch_order(self, symbol, side, order_list):
        param = {
            'symbol': symbol,
            'side': side,
            'ts': int(time.time()),
            'orders': order_list
        }
        # print(param)
        sign, paramStr = self.make_sign(pParams=json.dumps(param))
        data = {
            'access_key': self.apiKey, 'data': paramStr, 'sign': sign
        }
        # print('data',data)
        url = self.url + HTTP_BATCH_CREATE
        return self._request(url=url, data=json.dumps(data), method='post')

    def batch_cancel(self, order_id_list):
        param = {
            'ids':order_id_list,
            'ts': int(time.time())
        }
        # print(param)
        sign, paramStr = self.make_sign(pParams=json.dumps(param))
        data = {
            'access_key': self.apiKey, 'data': paramStr, 'sign': sign
        }
        # print(data)
        url = self.url + HTTP_BATCH_CANCEL_ORDER
        return self._request(url=url, data=json.dumps(data), method='post')

    def query_orderList(self, symbol, type):
        param = {
            'symbol': symbol,
            'type': type,
            'ts': int(time.time()),
        }
        sign = self.create_sign(param=param)
        param['access_key'] = self.apiKey
        param['sign'] = sign
        url = self.url + HTTP_QUERY_ORDER_LIST
        return self._request(url=url, data=param, method='get')

    def query_orderList_status(self, symbol, state, page, size):
        """

        :param symbol:
        :param state: padding/未成交，tx/未成交或部分成交,cancel/已经撤销，trade/完全成交，done/订单结束，包括完全成交和已撤销
        :param page:
        :param size: 每页显示数量，最大不能超过1024
        :return:
        """
        param = {
            'symbol': symbol,
            'state': state,
            'page': page,
            'size': size,
            'ts': int(time.time()),
        }
        sign = self.create_sign(param=param)
        param['access_key'] = self.apiKey
        param['sign'] = sign
        url = self.url + HTTP_QUERY_ORDER_LIST_STATUE
        return self._request(url=url, data=param, method='get')

    def deal_order_list(self, symbol, type, page, size):
        param = {
            'symbol': symbol,
            'type': type,
            'ts': int(time.time()),
            'page': page,
            'size': size
        }
        sign = self.create_sign(param=param)
        param['access_key'] = self.apiKey
        param['sign'] = sign
        url = self.url + HTTP_DEAL_RECORD
        return self._request(url=url, data=param, method='get')

    def order_info(self,order_id):
        param = {
            'order_id': order_id,
            'ts': int(time.time())
        }
        sign = self.create_sign(param=param)
        param['access_key'] = self.apiKey
        param['sign'] = sign
        url = self.url + HTTP_GET_ORDER_INFO
        return self._request(url=url, data=param, method='get')

    def get_depth(self, symbol, limit):
        param = {
            'symbol': symbol,
            'limit': limit
        }
        url = HTTP_TEST_DEPTH
        return self._request(url=url, data=param, method='get')

    def get_kline(self, symbol, limit, period):
        """

        :param symbol:
        :param limit: kline条数
        :param period: 时间类型， 1min/5min/15min/30min/1hour/4hour/1day/1week/1month
        :return:
        """
        param = {
            'symbol': symbol,
            'limit': limit,
            'ts': int(time.time()),
            'period': period
        }
        sign = self.create_sign(param=param)
        param['access_key'] = self.apiKey
        param['sign'] = sign
        url = self.url + HTTP_KLINE
        return self._request(url=url, data=param, method='get')

    def get_recharge_record(self, currency, page=None, page_size=None):
        param = {
            'coin_name': currency,
        }
        if page:
            param['page']=page
        if page_size:
            param['page_size'] = page_size

        print(json.dumps(param))
        # sign, paramStr = self.make_sign(pParams=json.dumps(param))
        # data = {
        #     'access_key': self.apiKey, 'data': paramStr, 'sign': sign
        # }
        # print(data)
        url = self.url + HTTP_RECHARGE_RECORD
        return self._request(url=url, data=json.dumps(param), method='post')

    def withdraw_deposit_record(self,currency,page=None,page_size=None):
        param = {
            'coin_name': currency,
        }
        if page:
            param['page'] = page
        if page_size:
            param['page_size'] = page_size

        # print(param)
        # sign, paramStr = self.make_sign(pParams=json.dumps(param))
        # data = {
        #     'access_key': self.apiKey, 'data': paramStr, 'sign': sign
        # }
        # print(data)
        url = self.url + HTTP_WITHDRAW_DEPOSIT_RECORD
        return self._request(url=url, data=json.dumps(param), method='post')

    def get_hold_currency(self,currency,page=None,page_size=None):
        param = {
            'coin_name': currency,
        }
        if page:
            param['page'] = page
        if page_size:
            param['page_size'] = page_size

        # print(param)
        # sign, paramStr = self.make_sign(pParams=json.dumps(param))
        # data = {
        #     'access_key': self.apiKey, 'data': paramStr, 'sign': sign
        # }
        # print(data)
        url = self.url + HTTP_HOLD_CURRENCY
        return self._request(url=url, data=json.dumps(param), method='post')

    def get_deal_record_all(self, user_id=None, startTime=None, endTime = None, page=None, page_size=None):
        param = {}
        if user_id:
            param['user_id'] = user_id
        if startTime:
            param['start'] = startTime
        if endTime:
            param['end'] = endTime
        if page:
            param['page'] = page
        if page_size:
            param['page_size'] = page_size
        # sign, paramStr = self.make_sign(pParams=json.dumps(param))
        # data = {
        #     'access_key': self.apiKey, 'data': paramStr, 'sign': sign
        # }
        # print(data)
        url = self.url + HTTP_DEAL_RECORD_ALL
        return self._request(url=url, data=json.dumps(param), method='post')

    def get_depthDetail(self):
        param = {}
        # sign = self.create_sign(param=param)
        # param['access_key'] = self.apiKey
        # param['sign'] = sign
        url = self.url + HTTP_DEPTHDETAIL
        return self._request(url=url, data=None, method='post')


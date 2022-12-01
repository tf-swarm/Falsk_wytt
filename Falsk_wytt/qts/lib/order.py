import datetime
import logging
import time

from qts.constants import USERS
from qts.lib.bttv_pymysql import CUD_data, read_data
from qts.utils.exchange.TAIBI.clientApi import TaBiApi
from qts.utils.exchange.TAIBI.taibiApi import CTB
from qts.utils.exchange.BINANCE.binanceApi import CBinance
from qts.utils.exchange.huobi.huobiApi import CHuobi
from qts.utils.exchange.Hoo.hooApi import Hoo


def create_order(msg):
    try:
        account_id, account_name = msg["account_id"], msg["account_name"]
        symbol_id, side, price, amount = msg["symbol"], msg["side"], msg["price"], msg["amount"]
        sql = "select * from t_account where account_id=%s and account_name=%s"
        data = [account_id, account_name]
        account = read_data(sql=sql, data=data)[0]
        exchange, api_key, secret_key = account['exchange'], account['api_key'], account['secret_key']
        order = None
        if exchange == 'BINANCE':
            api = CBinance(api_key, secret_key)
            symbol = symbol_id.replace("/", "")
        elif exchange == "HUOBI":
            api = CHuobi(api_key, secret_key)
            symbol = symbol_id.replace("/", "").lower()
        elif exchange == "Hoo":
            api = Hoo(api_key, secret_key, 'innovate')
            symbol = symbol_id.replace("/", "-")
        # elif exchange == "BITHUMB":
        #     index = symbol_id.index("/")
        #     symbol = str(symbol_id[:index])
        else:
            # TAIBI
            api = CTB(api_key, secret_key)
            symbol = symbol_id

        if side == "BUY":
            result = api.Buy(symbol, price, amount)
        else:
            result = api.Sell(symbol, price, amount)
        if result != -1:
            order = {"order_id": result, "status": "created"}
        return order
    except Exception as e:
        print("create order error:", e)
        return None


def cancel_order(user_id, member_id, order_id):
    api_key = USERS[user_id]['accounts'][member_id]['apikey']
    secret_key = USERS[user_id]['accounts'][member_id]['secretkey']
    symbol = USERS[user_id]['symbol']
    exchange = USERS[user_id]['exchange']
    if exchange == 'TAIBI':
        order_id_list = [int(order_id)]
        res = TaBiApi(key=api_key, secret=secret_key).batch_cancel(order_id_list=order_id_list)
        # res {'code': 10000, 'msg': 'ok'}
        if res and res.get('msg') == 'ok':
            order_info = {"order_id": order_id, "status": "canceled"}
            return order_info
        else:
            return False


def get_external_orders(user):
    from qts import redis_deal
    api_key, secret_key = user['api_key'], user['secret_key']
    exchange, symbol = user['exchange'], user['symbol']
    depth = redis_deal.hmget("{}".format(exchange), ["DEPTH"])
    res_info = (eval(depth[0]) if depth[0] else {})
    depth_info, deal_bids, deal_asks = {}, {}, {}
    spread_info = get_spreads(res_info, symbol)
    depth_info.update(spread_info)
    try:
        result = []
        if exchange == 'BINANCE':
            result = CBinance(api_key, secret_key).get_orders(symbol)
        elif exchange == 'HUOBI':
            result = CHuobi(api_key, secret_key).get_orders(symbol)
        elif exchange == 'Hoo':
            result = Hoo(api_key, secret_key, 'innovate').get_orders(symbol)
        else:
            if exchange == 'TAIBI':
                status = 1
                res = TaBiApi(key=api_key, secret=secret_key).query_orderList(symbol=symbol, type=status)
                result = (res.get('data') if res and res.get('code') == 10000 else [])
        if result:
            for order in result:
                # 方向  1买，2卖
                price, side = 0.0, 0
                if exchange == 'BINANCE':
                    direction = (1 if order['side'] == "BUY" else 2)
                    price, side = float(order['price']), direction
                if exchange == 'HUOBI':
                    direction = (1 if order['order_type'] == "sell-limit" else 2)
                    price, side = float(order['price']), direction
                elif exchange == 'Hoo':
                    direction = (1 if order['side'] == 1 else 2)
                    price, side = float(order['price']), direction
                else:
                    if exchange == 'TAIBI':
                        direction = (1 if order['opt'] == 1 else 2)
                        price, side = float(order['limit_price']), direction

                if side == 1:  # 买
                    bids = depth_info["bids"]
                    for index, buy_list in enumerate(bids):
                        buy_price = buy_list.get("price", 0)
                        if price == buy_price:
                            interior_volume = deal_order_amount(exchange, order)
                            external_volume = buy_list["amount"] - interior_volume
                            deal_bids["{}".format(price)] = {"interior": interior_volume, "external": external_volume}
                        else:
                            continue

                elif side == 2:  # 卖
                    asks = depth_info["asks"]
                    for index, sell_list in enumerate(asks):
                        if price == sell_list["price"]:
                            interior_volume = deal_order_amount(exchange, order)
                            external_volume = sell_list["amount"] - interior_volume
                            deal_asks["{}".format(price)] = {"interior": interior_volume, "external": external_volume}
                        else:
                            continue

        deal_info = deal_bids_and_asks(depth_info, deal_bids, deal_asks)
        return deal_info
    except Exception as e:
        logging.error("交易所:{},币对：{}错误：{}".format(exchange, symbol, e))
        return -1


def balance(account_id):
    sql = "select * from t_account where account_id=%s"
    data = [account_id]
    account = read_data(sql=sql, data=data)[0]
    exchange, api_key, secret_key = account['exchange'],  account['api_key'], account['secret_key']
    balances = {}
    if exchange == 'BINANCE':
        result = CBinance(api_key, secret_key).get_account()
        for data in result:
            if (float(data['free']) > 0 or float(data['locked']) > 0):
                asset = data['asset']
                balances[asset] = {}
                balances[asset]['available'] = float(data['free'])
                balances[asset]['locked'] = float(data['locked'])
    elif exchange == 'HUOBI':
        result = CHuobi(api_key, secret_key).get_accounts()
        if isinstance(result, list):
            for data in result:
                if (float(data['free']) > 0 or float(data['locked']) > 0):
                    asset = data['asset']
                    balances[asset] = {}
                    balances[asset]['available'] = float(data['free'])
                    balances[asset]['locked'] = float(data['locked'])
    # elif exchange == 'BITHUMB':
    #     pass
    elif exchange == 'Hoo':
        result = Hoo(api_key, secret_key, 'innovate').get_account()
        for data in result:
            if (float(data['free']) > 0 or float(data['locked']) > 0):
                asset = data['asset']
                balances[asset] = {}
                balances[asset]['available'] = float(data['free'])
                balances[asset]['locked'] = float(data['locked'])
    else:
        # TAIBI
        if exchange == 'TAIBI':
            res = TaBiApi(key=api_key, secret=secret_key).get_balance()
            if res and res.get('code') == 10000:
                for bal in res['data']:
                    if (float(bal['qty']) > 0 or float(bal['freeze_qty']) > 0):
                        balances[bal['symbol']] = {}
                        balances[bal['symbol']]['available'] = float(bal['qty'])
                        balances[bal['symbol']]['locked'] = float(bal['freeze_qty'])
    # print("balance----:", exchange, balances)
    return balances


def batch_create(dict):

    apikey = USERS[dict['user_id']]['accounts'][dict['member_id']]['apikey']
    secretkey = USERS[dict['user_id']]['accounts'][dict['member_id']]['secretkey']
    symbol = USERS[dict['user_id']]['symbol']
    exchange = USERS[dict['user_id']]['exchange']
    res = None
    orderNo = None
    if exchange == 'TAIBI':
        order_list = [
            {"price": dict['price'], "qty": dict['volume']},
        ]
        res = TaBiApi(key=apikey, secret=secretkey).batch_order(symbol=symbol,side= 0 if dict['side']=='BUY' else 1,order_list=order_list)
        if res and res.get('data'):
            orderNo = res['data'][0]

    if orderNo:
        if dict.get('sql') and dict['sql'] =='batch_order':
            sql = 'update t_batch_detail set order_id=%s,member_id=%s,status=%s where batch_detail_id=%s'
            data = [orderNo,dict['member_id'], 'place', dict['batch_detail_id']]
            try:
                CUD_data(sql, data)
            except Exception as e:
                logging.error('数据库写入失败:batch_detail_id %s'%dict['batch_detail_id'])
        if dict.get('sql') and dict['sql'] =='auto_batch_order':

            sql = 'insert into t_auto_batch_detail(auto_batch_detail_id,auto_batch_order_id,member_id,order_id,side,symbol,status,volume,price,created_date,user_id) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'
            data = [dict['auto_batch_detail_id'], dict['auto_batch_order_id'], dict['member_id'],orderNo,dict['side'],symbol,'placed',dict['volume'] ,dict['price'],datetime.datetime.now(),dict['user_id']]
            try:
                CUD_data(sql, data)
            except Exception as e:
                print(e)
                logging.error('数据库写入失败:auto_batch_detail_id %s' % dict['auto_batch_detail_id'])
    return res


def batch_cancel(dict):
    '''
    dict={
    'user_id':1,
    'member_id':179132,
    'order_id':'',
    'batch_detail_id':''
    }
    :param dict:
    :return:
    '''
    try:
        apikey = USERS[dict['user_id']]['accounts'][dict['member_id']]['apikey']
        secretkey = USERS[dict['user_id']]['accounts'][dict['member_id']]['secretkey']
    except Exception as e:
        print('ERRor', dict)
        apikey = None
        secretkey =None

    symbol = USERS[dict['user_id']]['symbol']
    exchange = USERS[dict['user_id']]['exchange']

    res = None
    if exchange == 'TAIBI':
        order_id_list = [int(dict['order_id'])]
        res = TaBiApi(key=apikey, secret=secretkey).batch_cancel(order_id_list=order_id_list)
        if res and res.get('msg')=='ok':
            res =True

    if res:
        if dict.get('sql') and dict['sql'] == 'batch_order':
            if dict.get('batch_detail_id'):
                sql = 'update t_batch_detail set status=%s where batch_detail_id=%s'
                data = ['canceled', dict['batch_detail_id']]
                try:
                    CUD_data(sql, data)
                except Exception as e:
                    logging.error('数据库写入失败:batch_detail_id %s'%dict['batch_detail_id'])
            else:
                pass
        if dict.get('sql') and dict['sql'] == 'auto_batch_order':
            if dict.get('auto_batch_detail_id'):
                sql = 'update t_auto_batch_detail set status=%s where auto_batch_detail_id=%s'
                data = ['canceled', dict['auto_batch_detail_id']]
                try:
                    CUD_data(sql, data)
                except Exception as e:
                    logging.error('数据库写入失败:auto_batch_detail_id %s'%dict['auto_batch_detail_id'])
            else:
                pass
    return {'orderId': dict['order_id'],'status':res}


def get_spreads(res_info, symbol):
    spread = res_info[symbol]
    dif_price = 0.0
    if len(spread['bids']) > 0 and len(spread['asks']) > 0:
        buy_one, sell_one = spread["bids"][0]["price"], spread['asks'][0]["price"]
        dif_price = round(2 * (sell_one - buy_one) / (buy_one + sell_one) * 100, 2)
        # print("--dif_price--:", sell_one, buy_one, dif_price)
    # 处理盘口数目条数
    depth_info = {"asks": spread['asks'][:20], "bids": spread["bids"][:20], "dif_price": dif_price, "time": time.time() * 1000}
    return depth_info


def deal_order_amount(exchange, order):
    interior_volume = 0.0
    if exchange == 'BINANCE':
        interior_volume = float(order['origQty']) - float(order['executedQty'])
    elif exchange == 'HUOBI':
        interior_volume = float(order['amount']) - float(order['filled-amount'])
    elif exchange == 'Hoo':
        interior_volume = float(order['quantity']) - float(order['match_qty'])
    else:
        if exchange == 'TAIBI':
            interior_volume = float(order['num']) - float(order['traded_num'])
    return interior_volume


def deal_bids_and_asks(depth_info, deal_bids, deal_asks):
    for index, bids in enumerate(depth_info["bids"]):
        bids_price = str(bids["price"])
        if bids_price in deal_bids:
            bids_info = deal_bids[bids_price]
            interior, external = bids_info["interior"], bids_info["external"]
        else:
            interior = 0
            external = bids["amount"]
        depth_info["bids"][index].update({"external": external, "interior": interior})

    for index, asks in enumerate(depth_info["asks"]):
        asks_price = str(asks["price"])
        if asks_price in deal_asks:
            asks_info = deal_asks[asks_price]
            interior, external = asks_info["interior"], asks_info["external"]
        else:
            interior = 0
            external = asks["amount"]
        depth_info["asks"][index].update({"external": external, "interior": interior})
    return depth_info


if __name__=='__main__':
    print("res")
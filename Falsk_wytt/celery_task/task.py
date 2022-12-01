# coding:utf-8
from celery_task import celery
from datetime import datetime, timedelta
import time
from threading import Thread
from qts.lib.bttv_pymysql import read_data, CUD_data, CUD_batch
from qts.utils.exchange.BINANCE.binanceApi import CBinance
from qts.utils.exchange.huobi.huobiApi import CHuobi
from qts.utils.exchange.Hoo.hooApi import Hoo
from qts.utils.exchange.BITHUMB.bithumbApi import CBithumb
from qts.utils.exchange.TAIBI.taibiApi import CTB
from qts.utils.quotation.quotApi import QuotApi
from qts.lib.power import get_exchange_list
from qts.utils.tool.tool import Time
import json
from qts import redis_deal

# @celery.task()
# def scheduled_task(*args, **kwargs):
#     now_time = time.strftime('%Y.%m.%d %H:%M:%S', time.localtime(time.time()))
#     print(now_time)


@celery.task()
def account_balance(*args, **kwargs):
    """账户余额数据"""
    keys = 'timers_task:%d:%s' % (2, 'account_balance')
    result = redis_deal.hmget(keys, ["state", "insert_time"])
    if result[0]:
        if int(result[0]) == 1:
            return 0
        else:
            redis_deal.hmset(keys, {"state": 1, "insert_time": Time.current_ts()})
    else:
        redis_deal.hmset(keys, {"state": 0, "insert_time": Time.current_ts()})

    deal_symbol, record_list, now_time = ['USDT', 'HUSD'], [], datetime.now()
    sql = "select * from t_account"
    account_list = read_data(sql=sql)
    for account in account_list:
        exchange, account_id, account_name = account['exchange'], account['account_id'], account['account_name']
        api_key, secret_key = account['api_key'], account['secret_key']
        json_list, symbol_info, balance_list = [], {}, []
        if exchange == 'BINANCE':
            api = CBinance(api_key, secret_key)
            balance_list = api.get_account()

        elif exchange == 'HUOBI':
            api = CHuobi(api_key, secret_key)
            balance_list = api.get_accounts()

        # elif exchange == 'BITHUMB':
        # 	api = CBithumb(api_key, secret_key)
        # 	balance_list = api.get_account(symbol)

        elif exchange == 'Hoo':
            api = Hoo(api_key, secret_key, 'innovate')
            balance_list = api.get_account()

        for balance in balance_list:
            asset, last_price = balance["asset"], 1
            if asset not in deal_symbol:
                symbol_str = "{}/USDT".format(asset)
                if exchange == 'BINANCE':
                    symbol = symbol_str.replace("/", "")

                elif exchange == 'HUOBI':
                    symbol = symbol_str.replace("/", "").lower()

                elif exchange == 'BITHUMB':
                    index = symbol_str.index("/")
                    symbol = str(symbol_str[:index])

                elif exchange == 'Hoo':
                    symbol = symbol_str.replace("/", "-")

                ticker = api.get_ticker(symbol)
                last_price = ticker.get("lastprice", 1)

            balance.update({"price": last_price})
            json_list.append(balance)

        # price = int(float(balance["free"]) * last_price)
        # if price > 1:
        # 	balance.update({"price": last_price})
        # 	json_list.append(balance)
        # else:
        # 	continue

        if len(json_list) > 0:
            record_info = (now_time, account_id, account_name, json.dumps(json_list))
            record_list.append(record_info)

    # 批量插入数据
    sql = 'insert into t_balance_count(insert_date,account_id,account_name,json_info) values (%s,%s,%s,%s)'
    data = record_list
    try:
        CUD_batch(sql, data)
    except Exception as e:
        print("insert account balance error--:", e)

    redis_deal.hmset(keys, {"state": 0, "insert_time": Time.current_ts()})
    print('{}_update_time_{}'.format(keys, Time.current_ts()))


@celery.task()
def trading_record(*args, **kwargs):
    """ 交易数据"""
    keys = 'timers_task:%d:%s' % (2, 'trading_record')
    result = redis_deal.hmget(keys, ["state", "insert_time"])
    if result[0]:
        if int(result[0]) == 1:
            return 0
        else:
            redis_deal.hmset(keys, {"state": 1, "insert_time": Time.current_ts()})
    else:
        redis_deal.hmset(keys, {"state": 0, "insert_time": Time.current_ts()})

    sql = "select * from t_account"
    account_list = read_data(sql=sql)
    for account in account_list:
        exchange, account_id, account_name = account['exchange'], account['account_id'], account['account_name']
        api_key, secret_key = account['api_key'], account['secret_key']
        symbol_list = get_exchange_list(exchange)

        if symbol_list:
            record_list = []
            children = symbol_list[0]["children"]
            for info in children:
                trades_list = []
                symbol = info["name"].replace("/", "")
                if exchange == 'BINANCE':
                    api = CBinance(api_key, secret_key)
                    trades_list = api.get_trades(symbol)

                elif exchange == 'HUOBI':
                    api = CHuobi(api_key, secret_key)
                    symbols = symbol.lower()
                    date_end = datetime.strptime(time.strftime("%Y-%m-%d", time.localtime()), '%Y-%m-%d')
                    # 获取mysql最后一条记录的时间
                    sql = "select insert_date from t_trades_record order by insert_date desc limit 1"
                    res_info = read_data(sql=sql)
                    if not res_info:
                        date_start = datetime.strptime(Time.getdate(120), '%Y-%m-%d')
                        while date_start < date_end:
                            date_start += timedelta(days=1)
                            str_time = date_start.strftime('%Y-%m-%d') + " 00:00:00"
                            stamp_time = Time.str_to_timestamp(str_time) * 1000
                            trades = api.get_trades(symbols, stamp_time)
                            if len(trades) > 0:
                                trades_list.extend(trades)
                    else:
                        date_start = res_info[0].get("insert_date", 0)
                        print("--date_start--", date_start, type(date_start))

                elif exchange == 'Hoo':
                    symbols = symbol.replace("/", "-")
                # api = Hoo(api_key, secret_key, 'innovate')
                # trades_list = api.get_trades(symbols)
                elif exchange == 'BITHUMB':
                    pass

                for json_data in trades_list:
                    order_id = str(json_data["orderId"])
                    is_buyer = 0
                    if exchange == 'BINANCE':
                        is_buyer = (1 if json_data["isBuyer"] else 0)
                    elif exchange == 'HUOBI':
                        is_buyer = (1 if json_data["isBuyer"] == "taker" else 0)
                    elif exchange == 'Hoo':
                        is_buyer = (1 if json_data["side"] == 1 else 0)
                        qty = json_data["volume"]
                        json_data.update({"qty": qty})

                    date_time = Time.timestamp_to_str(json_data["time"] / 1000)
                    # 1.判断订单ID是否存在
                    sql = "select * from t_trades_record where order_id=%s"
                    api_data = [order_id]
                    result = read_data(sql=sql, data=api_data)
                    if not result:
                        # 2.添加记录到列表
                        json_data.update({"date_time": date_time, "is_buyer": is_buyer})
                        record_info = (
                        account_id, account_name, date_time, order_id, symbol, is_buyer, json.dumps(json_data))
                        record_list.append(record_info)
                    else:
                        continue

            # 3.批量插入数据
            sql = 'insert into t_trades_record(account_id,account_name,insert_date,order_id,symbol,is_buyer,json_info) values (%s,%s,%s,%s,%s,%s,%s)'
            data = record_list
            try:
                CUD_batch(sql, data)
            except Exception as e:
                print("insert account trades error--:", e)
        else:
            continue

    redis_deal.hmset(keys, {"state": 0, "insert_time": Time.current_ts()})
    print('{}_update_time_{}'.format(keys, Time.current_ts()))


@celery.task()
def deposit_withdraw_history(*args, **kwargs):
    """充提币记录"""
    keys = 'timers_task:%d:%s' % (2, 'deposit_withdraw_history')
    result = redis_deal.hmget(keys, ["state", "insert_time"])
    if result[0]:
        if int(result[0]) == 1:
            return 0
        else:
            redis_deal.hmset(keys, {"state": 1, "insert_time": Time.current_ts()})
    else:
        redis_deal.hmset(keys, {"state": 0, "insert_time": Time.current_ts()})

    # sql = "select * from t_account"
    # account_list = read_data(sql=sql)
    # for account in account_list:
    #     exchange, account_id, account_name = account['exchange'], account['account_id'], account['account_name']
    #     create_time = account['create_date']
    #     api_key, secret_key = account['api_key'], account['secret_key']
    #     json_list, now_time = [], int(time.time())
    #
    #     if exchange == 'BINANCE':
    #         api = CBinance(api_key, secret_key)
    #         # 1.判断订单ID是否存在
    #         sql = "select insert_date from t_deposit_withdraw"
    #         history_data = None
    #         result = read_data(sql=sql, data=history_data)
    #         if not result:
    #             # start_time = Time.datetime_to_timestamp(create_time)
    #             start_time = 1546272000 * 1000  # 2019-01-01 00:00:00
    #         else:
    #             date_time = result[-1:][0]["insert_date"]
    #             start_time = Time.datetime_to_timestamp(date_time) * 1000
    #
    #         deposit_list = api.get_sub_deposit_history(start_time)
    #         for deposit in deposit_list:
    #             tran_id, transfer_type = deposit["tranId"], deposit["type"]
    #             insert_date = Time.timestamp_to_str(int(deposit["time"] / 1000))
    #
    #             sql = "select tran_id from t_deposit_withdraw where tran_id=%s"
    #             api_data = [tran_id]
    #             result = read_data(sql=sql, data=api_data)
    #             if not result:
    #                 # 2.添加记录到列表
    #                 deposit.update({"account_name": account_name})
    #                 record_info = (tran_id, insert_date, account_id, transfer_type, json.dumps(deposit))
    #                 json_list.append(record_info)
    #             else:
    #                 continue
    #         # 3.批量插入数据
    #         sql = 'insert into t_deposit_withdraw(tran_id,insert_date,account_id,transfer_type,json_info) values (%s,%s,%s,%s,%s)'
    #         data = json_list
    #         try:
    #             CUD_batch(sql, data)
    #         except Exception as e:
    #             print("insert account deposit error--:", e)

    redis_deal.hmset(keys, {"state": 0, "insert_time": Time.current_ts()})
    print('{}_update_time_{}'.format(keys, Time.current_ts()))
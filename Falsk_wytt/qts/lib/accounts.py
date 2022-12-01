
import datetime
import os
import threading
from time import sleep

from qts.constants import USERS
from qts.lib.bttv_pymysql import read_data, CUD_data
from qts.lib.order import balance
from qts.lib.time_uuid import create_time_uuid
import random


def get_user_info():
    sql = "select * from t_user"
    data = None
    user_list = read_data(sql=sql)
    for user in user_list:
        user_util(user)

    print('*********用户系统加载完成***************')


def user_util(user):
    # from qts.lib.order_util import OrderUtils
    user_id, account_ids = user['user_id'], user['account_ids']
    USERS[user_id] = {}
    # USERS[user['user_id']]['exchange'] = user['exchange']
    # USERS[user['user_id']]['symbol'] = user['symbol']
    # USERS[user['user_id']]['order_utils'] = OrderUtils(user_id=user['user_id'])
    # 获取余额
    threading.Thread(target=get_account, args=(user_id, account_ids)).start()
    # 记录资产
    # threading.Thread(target=account_balance_record, args=(user['user_id'],)).start()
    # if user['exchange'] == 'TAIBI':
    #     USERS[user_id]['price_precision'] = 6
    #     USERS[user_id]['volume_precision'] = 4
    #     USERS[user_id]['min_order_volume'] = 0.01
    #     USERS[user_id]['rate'] = 0.002
    # else:
    USERS[user_id]['price_precision'] = 6
    USERS[user_id]['volume_precision'] = 4
    USERS[user_id]['min_order_volume'] = 0.02
    USERS[user_id]['rate'] = 0.002


def get_account(user_id, account_ids):
    aid_info = tuple(account_ids.split(","))
    sql = "select * from t_account where account_id in %s"
    data = [aid_info]
    account_list = read_data(sql=sql, data=data)
    # print("--account_list--", account_list)

    if not USERS[user_id].get('accounts'):
        USERS[user_id]['accounts'] = {}

    for account in account_list:
        # print("--account--:", account, type(account))
        if USERS[user_id]['accounts'].get(account['account_id']):
            continue
        else:
            USERS[user_id]['accounts'][account['account_id']] = {}

        account_id = account['account_id']
        USERS[user_id]['accounts'][account_id]['account_name'] = account['account_name']
        USERS[user_id]['accounts'][account_id]['exchange'] = account['exchange']
        USERS[user_id]['accounts'][account_id]['api_key'] = account['api_key']
        USERS[user_id]['accounts'][account_id]['secret_key'] = account['secret_key']
        # USERS[user_id]['accounts'][account['account_id']]['is_enabled'] = True if account['is_enabled'].decode() =='\x01'else False
        # 获取余额
        threading.Thread(target=get_account_balance, args=(user_id, account_id)).start()

    # print("---get_account---:", USERS)


def get_account_balance(user_id, account_id):
    while True:
        now_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        res = balance(account_id=account_id)
        if res:
            USERS[user_id]['accounts'][account_id]['balance'] = res
            USERS[user_id]['accounts'][account_id]['balance']['time'] = now_time

        sleep(5)


def account_balance_record(user_id):
    """每两小时记录一次资产
    :param user_id:
    :return:
    """
    sleep(5)
    while True:
        sql = 'insert into t_record_fund(id,created_date,member_id,fund,user_id) values (%s,%s,%s,%s,%s)'
        for account_key, account_volume in USERS[user_id]['accounts'].items():

            if account_volume.get('balance'):
                data = [create_time_uuid(), datetime.datetime.now(), account_key, str(account_volume['balance']), user_id]
                CUD_data(sql, data)

        print('用户%s资产记录完成 %s'%(user_id, datetime.datetime.now()))
        sleep(60*60*2)


def choose_account(user_id, category=None):
    if USERS.get(user_id) and USERS[user_id].get('accounts'):
        pass
    else:
        sleep(2)
    account_list = []
    if category:
        for account_id, account_info in USERS[user_id]['accounts'].items():
            if account_info['category'] == category and account_info['is_enabled'] == True:
                account_list.append(account_id)
    else:
        account_list = [key for key in USERS[user_id]['accounts'].keys()]
    # print(account_list)
    return account_list


if __name__ == '__main__':
    get_user_info()


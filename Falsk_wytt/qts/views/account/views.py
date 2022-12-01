
import datetime
import json
import time
import os
from qts.lib.crypto_demo import CryptoRsa
from flask import request, current_app, session, jsonify
from qts import db
from qts.constants import USERS
from qts.lib.check_login import login_check
from qts.models import Account, User, Exchange
from qts.views.account import account_blue
from qts.lib.power import get_exchange_list, get_page_power, get_account_symbol


@account_blue.route('/paging', methods=['POST'])
@login_check
def account_paging():
    """
    {"page":1,"size":100,"sort":"WEIGHT","order":"DESC",
    "query":{"userId":5,"date":"2019-10-09T03:37:06.623Z","enabled":true}}
    翻页
    """
    response = {
        'status': 0,
        'error': None,
        'data': None,
        'message': 'suc'
    }
    power_id = request.json.get('power_id')
    page = request.json.get('page')
    size = request.json.get('size')
    query = request.json.get('query')
    user_id = session.get('user_id')
    role_id = session.get('role_id')
    accounts, account_list = [], []
    if power_id:
        deal_power = get_page_power(role_id, power_id)
    else:
        deal_power = {}
    res = User.query.filter(User.user_id == user_id).first()
    account_id = query.get("account_name")
    if role_id == 0:
        if account_id:
            account_info = Account.query.filter_by(account_id=account_id).first()
            account_list.append(account_info)
        else:
            account_list = Account.query.all()
    else:
        # 1.根据user_id得到账户account_ids
        aid_list = res.account_ids.split(",")
        # 2.遍历account_id列表，获取account数据
        if account_id:
            for aid in aid_list:
                if account_id == aid:
                    account_info = Account.query.filter_by(account_id=account_id).first()
                    account_list.append(account_info)
                else:
                    continue
        else:
            for aid in aid_list:
                account_info = Account.query.filter_by(account_id=aid).first()
                account_list.append(account_info)

    res_exchange, exchange_keys = {}, {}
    res_info = Exchange.query.all()
    for res_one in res_info:
        exchange_keys[res_one.ex_id] = res_one
        if str(res_one.exchange_level) == "0":
            res_exchange[res_one.ex_id] = {
                "id": res_one.ex_id,
                "Name": res_one.exchange_name,
                "exchange_id": res_one.exchange_id,
            }
    for account in account_list:
        if account:
            symbol_result = {}
            symbol_list = account.symbol_ids.split(",")
            res_dict = account.to_dict()
            account_id = res_dict["id"]
            secret_key = res_dict["secret_key"]
            if role_id == 0:
                secret_string = secret_key
            else:
                if deal_power and deal_power.get("secret_key", 0):
                    secret_string = secret_key
                else:
                    secret_string = "*" * 40
            symbol_result.update({
                "id": account_id,
                "account_name": res_dict["account_name"],
                "exchange": res_dict["exchange"],
                "api_key": res_dict["api_key"],
                "secret_key": secret_string,
                "create_date": res_dict["create_date"],
                "children": []
            })
            symbol_result["children"] = get_account_symbol(exchange_keys, symbol_list)
            # print("--USERS--", USERS)
            if USERS[user_id]['accounts'].get(account_id) and USERS[user_id]['accounts'][account_id].get('balance'):
                symbol_result['balance'] = USERS[user_id]['accounts'][account_id]['balance']
            accounts.append(symbol_result)
    exchange_list = list(res_exchange.values())
    response.update({"data": accounts, "exchange": exchange_list, "power": deal_power})
    return response


@account_blue.route('/save', methods=['POST'])
@login_check
def create_account():
    """
        添加账户
        修改账户
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
    response = {
        'data': None,
        'error': None,
        'status': 0,
        'success': True,
        'timestamp': timestamp
    }
    created_date = datetime.datetime.now()
    account_id = request.json.get("id")
    exchange = request.json.get("exchange")
    account_name = request.json.get("account_name")
    access_key = request.json.get("api_key")
    cipher_text = request.json.get("secret_key")
    if not all([exchange, account_name, access_key, cipher_text]):
        response.update({"error": "参数不足", "status": 1, "success": False})
        return response
    try:
        account = Account.query.filter(Account.account_id == account_id).first()
    except Exception as e:
        current_app.logger.error(e)
        response.update({"error": "数据查询失败", "status": 1, "success": False})
        return response
    path = os.path.dirname(__file__).split('qts')[0]
    secret_key = CryptoRsa(password='quant2021').rsa_decrypto(ciphertext=cipher_text, path=path)
    if account:
        account.exchange = exchange
        account.account_name = account_name
        account.api_key = access_key
        account.secret_key = secret_key
    else:
        res = Account.query.filter(Account.account_name == account_name).first()
        if res:
            response.update({"error": "账户名称已存在", "status": 1, "success": False})
            return response
        else:
            account = Account(
                exchange=exchange,
                account_name=account_name,
                api_key=access_key,
                secret_key=secret_key,
                symbol_ids="",
                create_date=created_date,
            )
        try:
            db.session.add(account)
        except Exception as e:
            current_app.logger.error(e)
            response.update({"error": "添加失败", "status": 1, "success": False})
            return response

    db.session.commit()
    account_dict = account.to_dict()
    # 保存后重新读取账户信息
    # get_account(user_id=user_id)
    response.update({"data": account_dict})
    return response


@account_blue.route("/remove", methods=['GET'])
@login_check
def account_remove():
    """
    删除账户
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
    response = {
        'data': None,
        'error': None,
        'status': 0,
        'success': True,
        'timestamp': timestamp
    }
    # user_id = session.get('user_id')
    account_id = request.args.get("accountId")
    if not account_id:
        response.update({"error": "参数错误", "status": 1, "success": False})
        return response
    try:
        account = Account.query.get(account_id)
    except Exception as e:
        current_app.logger.error(e)
        response.update({"error": "获取账号失败", "status": 1, "success": False})
        return response
    if account:
        try:
            # 修改user的账户列表权限
            user_list = User.query.order_by().all()
            account_id_str = str(account_id)
            for data in user_list:
                user_info = data.to_dict()
                account_str = user_info["account_ids"]
                account_list = account_str.split(",")
                if account_id_str in account_list:
                    account_list.remove(account_id_str)
                    result = Account.query.get(account_id)
                    result.account_ids = account_list
                    db.session.commit()
                else:
                    continue
            db.session.delete(account)
        except Exception as e:
            current_app.logger.error(e)
            response.update({"error": "删除失败", "status": 1, "success": False})
            return response
    return response


@account_blue.route("/symbol", methods=['GET'])
@login_check
def get_all_symbol():
    """获取所有币种数据"""
    response = {
        "status": 0,
        "error": None,
        "data": None,
        "msg": "suc"
    }

    exchange = request.args.get("exchange")
    symbol_list = get_exchange_list(exchange)
    response.update({"data": symbol_list})
    return response


@account_blue.route("/update_symbol", methods=['POST'])
@login_check
def update_symbol_right():
    response = {
        "status": 0,
        "error": None,
        "data": None,
        "msg": "suc"
    }
    account_id = request.json.get('account_id')
    symbol_str = request.json.get('symbol_ids')
    print("--update_symbol--:", account_id, symbol_str)
    res = Account.query.filter(Account.account_id == account_id).first()
    res.symbol_ids = symbol_str
    db.session.commit()
    return response



import json

import requests
from flask import session, request, jsonify

from qts.constants import DEPTH, USERS, THE_LATEST_DEAL, DEPTHCHART
from qts.lib.check_login import login_check
from qts.lib.order import create_order, cancel_order, get_external_orders
from qts.views.order import order_blue
from qts import redis_deal
from qts.models import Account
from qts.lib.power import get_page_power


@order_blue.route('/depth', methods=['GET'])
def depth():
    response = {
        'status': 0,
        'error': None,
        'data': None,
        'message': 'suc'
    }
    role_id = session.get('role_id')
    account_id = request.args.get('accountId')
    account_name = request.args.get('accountName')
    symbol_id = request.args.get('symbol')
    power_id = 102
    deal_power = get_page_power(role_id, power_id)
    res = Account.query.filter_by(account_id=account_id, account_name=account_name).first()
    if res:
        exchange = res.exchange
        result = redis_deal.hmget("{}".format(exchange), ["DEPTH"])
        depth_info = (eval(result[0]) if result[0] else {})
        if exchange == "BINANCE":
            symbol = symbol_id.replace("/", "")
        elif exchange == "HUOBI":
            symbol = symbol_id.replace("/", "").lower()
        # elif exchange == "BITHUMB":
        #     symbol = symbol_id
        elif exchange == "Hoo":
            # symbol = "WTA-USDT"
            symbol = symbol_id.replace("/", "-")
        else:
            # TAIBI
            symbol = symbol_id

        if depth_info.get(symbol):
            user_info = res.to_dict()
            user_info.update({"symbol": symbol})
            depth_list = get_external_orders(user_info)
            response.update({"data": depth_list})
    response.update({"power": deal_power})
    return jsonify(response)


@order_blue.route('/create', methods=["POST"])
@login_check
def create_order_():
    response = {
        'status': 0,
        'error': None,
        'data': None,
        'message': 'suc'
    }
    user_id = session.get('user_id')
    account_id = request.json.get('accountId')
    account_name = request.json.get('accountName')
    symbol = request.json.get('symbol')
    side = request.json.get('side')
    order_type = request.json.get('type')
    price = request.json.get('price')
    volume = request.json.get('volume')
    if not all([account_id, account_name, symbol, side, order_type, price, volume]):
        response.update({"status": 1, "error": "参数错误", "message": "fail"})
        return response

    order_info = {"account_id": account_id, "account_name": account_name,
                  "symbol": symbol, "side": side, "price": float(price), "amount": float(volume)}
    res = create_order(order_info)
    if res:
        response['data'] = res
    else:
        error = ("买入" if side == "BUY" else "卖出")
        response.update({"status": 1, "error": "{}失败".format(error), "message": "fail"})
    return response


@order_blue.route('/cancel', methods=["GET"])
@login_check
def cancel_order_():
    response = {
        'status': 0,
        'error': None,
        'data': None,
        'message': 'suc'
    }
    user_id = session.get('user_id')
    member_id = request.args.get('member_id')
    order_id = request.args.get('orderId')
    res = cancel_order(user_id=user_id, member_id=member_id, order_id=order_id)
    if res:
        response['data'] = res
    else:
        response['status'] = 1
        response['error'] = '失败'
        response['message'] = 'fail'
    return response



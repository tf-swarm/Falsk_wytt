import datetime
import threading
from flask import request, session, current_app
from sqlalchemy import and_

from qts import db, constants
from qts.lib.check_login import login_check
from qts.lib.time_uuid import create_time_uuid
from . import dampingOrder_blue
from qts.models import DampingOrder, Account
import json
from qts import redis_deal
from strategy.strategyManager import strategyManager
from qts.lib.power import get_page_power


@dampingOrder_blue.route("/findPage", methods=['POST'])
@login_check
def find_page():
    response = {
        "status": 0,
        "error": None,
        "data": None,
        "msg": "suc"
    }
    exchange_list, damping_list = [], []
    total = 0
    now_time = datetime.datetime.now()
    start_date = str(datetime.date(2020, 1, 1))
    end_date = str(now_time + datetime.timedelta(seconds=2))
    damping_order_id = request.json.get('damping_id')
    power_id = request.json.get('power_id')
    role_id = session.get('role_id')
    page = request.json.get('page')
    size = request.json.get('size')
    sort_ = request.json.get('sort')
    order = request.json.get('order')
    query = request.json.get('query')

    column_dict = {
        'damping_order_id': DampingOrder.damping_order_id.desc(),
        'created_date': DampingOrder.created_date.desc(),
        'updated_date': DampingOrder.updated_date.desc(),
        'user_id': DampingOrder.user_id.desc(),
    }
    if sort_ in column_dict.keys():
        pass
    else:
        sort_ = 'created_date'

    if damping_order_id:
        damping_order = DampingOrder.query.filter_by(damping_order_id=damping_order_id).first()
        damping_info = damping_order.to_dict()
        json_info = json.loads(damping_info.get("json_info"))
        damping_id, create_time, is_enabled = damping_info.get("id"), damping_info.get("created_date"), damping_info.get("is_enabled")
        json_info.update({
            "id": damping_id, "damping_id": damping_id, "is_enabled": is_enabled, "created_date": create_time
        })
        damping_list.append(json_info)
        total = len(damping_list)
    else:
        if query:
            user_id = query.get("userId")
            start_time = (query['startDate'] if "startDate" in query else start_date)
            end_time = (query['endDate'] if "endDate" in query else end_date)
            if order == "ASCE":
                damping_data = DampingOrder.query.filter(and_(DampingOrder.user_id == user_id, DampingOrder.created_date >= start_time,
                                                          DampingOrder.created_date <= end_time)).order_by(sort_)
            else:
                damping_data = DampingOrder.query.filter(
                    and_(DampingOrder.user_id == user_id, DampingOrder.created_date.__ge__(start_time),
                         DampingOrder.created_date.__le__(end_time))).order_by(column_dict[sort_])
            if damping_data:
                p_age = damping_data.paginate(page=page, per_page=size)
                total = p_age.total  # 查询返回的记录总数
                damping_data = p_age.items
            for res in damping_data:
                bucket_dict = res.to_dict()
                json_info = json.loads(bucket_dict.get("json_info"))
                damping_id, create_time, is_enabled = bucket_dict.get("id"), bucket_dict.get("created_date"), bucket_dict.get("is_enabled")
                json_info.update({
                    "id": damping_id, "damping_id": damping_id, "is_enabled": is_enabled, "created_date": create_time
                })
                damping_list.append(json_info)
        else:
            response['error'] = '参数不全'

    damping_info = {"total": total, "rows": damping_list}
    if power_id:
        deal_power = get_page_power(role_id, power_id)
    else:
        deal_power = {}
    response.update({"data": damping_info, "power": deal_power})
    print("--response--", response)
    return response


@dampingOrder_blue.route("/save", methods=['POST'])
@login_check
def save_args():
    created_date = datetime.datetime.now()
    stamp = created_date.strftime("%Y%m%d%H%M%S%f")[:-3]
    updated_date = created_date
    response = {
        'status': 0,
        'error': None,
        'data': None,
        'msg': "suc"
    }
    user_id = session.get('user_id')
    damping_order_id = request.json.get('id')
    account_id = request.json.get('account_id')  # 下单账户ID
    account_name = request.json.get('account_name')
    symbol = request.json.get('symbol')
    hold_risk = request.json.get('hold_risk_aversion')
    target_hold = request.json.get('target_hold_qty')
    min_order = request.json.get('min_order_qty')
    max_order = request.json.get('max_order_qty')
    best_price = request.json.get('best_price_bias')
    price_range = request.json.get('price_range')
    order_count = request.json.get('order_count')
    pre_precision = request.json.get('price_precision')
    vol_precision = request.json.get('volume_precision')
    is_enabled = 0
    result = Account.query.filter_by(account_id=account_id).first()
    if not result:
        response.update({"error": "账户不存在", "success": False, "status": 101})
    else:
        exchange = result.exchange
        bucket_info = {
            "exchange": exchange, "symbol": symbol, "account_id": account_id, "account_name": account_name, "hold_risk_aversion": float(hold_risk),
            "target_hold_qty": int(target_hold), "min_order_qty": int(min_order), "max_order_qty": int(max_order),
            "best_price_bias": float(best_price), "price_range": float(price_range), "order_count": int(order_count),
            "price_precision": int(pre_precision), "volume_precision": int(vol_precision)
        }
        if damping_order_id:
            try:
                damping_info = DampingOrder.query.filter(DampingOrder.damping_order_id == damping_order_id).first()
                if damping_info:
                    damping_info.exchange = exchange
                    damping_info.symbol = symbol
                    damping_info.is_enabled = is_enabled
                    damping_info.json_info = json.dumps(bucket_info)
                    damping_info.created_date = damping_info.created_date
                    damping_info.updated_date = updated_date
                    damping_info.user_id = user_id

                    db.session.commit()

                    response['success'] = True
                    response['response'] = damping_order_id
                else:
                    response['status'] = 104
                    response['success'] = False
                    response['error'] = "未知ID"
            except Exception as e:
                print(e)
                response['status'] = 101
                response['success'] = False
                response['error'] = e
            finally:
                response['timestamp'] = stamp
        else:
            damping_id = create_time_uuid()
            try:
                damping_order = DampingOrder(
                    damping_order_id=damping_id,
                    exchange=exchange,
                    symbol=symbol,
                    is_enabled=is_enabled,
                    json_info=json.dumps(bucket_info),
                    created_date=created_date,
                    updated_date=updated_date,
                    user_id=user_id
                )

                db.session.add(damping_order)
                db.session.commit()

                response['success'] = True
                response['response'] = damping_order.damping_order_id
            except Exception as e:
                print(e)
                response['status'] = 101
                response['success'] = False
                response['error'] = e
            finally:
                response['timestamp'] = stamp
        print("--response--", response)
    return response


@dampingOrder_blue.route("/start", methods=['GET'])
@login_check
def start():
    response = {
        'status': 0,
        'error': None,
        'data': None,
        'msg': 'suc'
    }
    user_id = session.get('user_id')
    damping_order_id = request.args.get('id')
    damping_info = DampingOrder.query.filter(DampingOrder.damping_order_id == damping_order_id).first()
    if damping_info:
        if damping_info.is_enabled == 0:
            is_status = 1
            damping_info.is_enabled = is_status

            json_info = json.loads(damping_info.json_info)
            account_id, account_name = json_info.get("account_id"), json_info.get("account_name")
            account = Account.query.filter(Account.account_id == account_id, Account.account_name == account_name).first()
            if account:
                account_info = account.to_dict()
                api_key, secret_key = account_info.get("api_key"), account_info.get("secret_key")
                json_info.update({"strategy_id": damping_order_id, "api_key": api_key, "secret_key": secret_key})

                strategy = {"{}".format(damping_order_id): is_status}
                redis_deal.hmset("strategy", strategy)
                print("--start_dampingOrder--", is_status, json_info)
                strategyManager.run("dampingorder", json_info)
                db.session.commit()
                response['status'] = 0
                response['msg'] = '开启成功'
            else:
                response['status'] = 101
                response['msg'] = '下单账户异常'
        else:
            response['status'] = 102
            response['msg'] = '该对阻尼挂单策略已开启'
    else:
        response['status'] = 104
        response['msg'] = '未知ID'

    return response


@dampingOrder_blue.route("/stop", methods=['GET'])
@login_check
def stop():
    response = {
        'status': 0,
        'error': None,
        'data': None,
        'msg': 'suc'
    }
    damping_order_id = request.args.get('id')
    damping_info = DampingOrder.query.filter(DampingOrder.damping_order_id == damping_order_id).first()
    if damping_info:
        if damping_info.is_enabled == 1:
            is_status = 0
            damping_info.is_enabled = is_status
            strategy = {"{}".format(damping_order_id): is_status}
            redis_deal.hmset("strategy", strategy)
            db.session.commit()

            response['status'] = 0
            response['msg'] = '关闭成功'
        else:
            response['status'] = 103
            response['msg'] = '该阻尼挂单策略已关闭'
    else:
        response['status'] = 104
        response['msg'] = "未知ID"

    return response


@dampingOrder_blue.route("/remove", methods=['GET'])
@login_check
def remove():
    response = {
        'status': 0,
        'error': None,
        'data': None,
        'msg': 'suc'
    }
    damping_order_id = request.args.get('id')
    res = DampingOrder.query.filter(DampingOrder.damping_order_id == damping_order_id).first()
    if res:
        is_status = 2
        strategy = {"{}".format(damping_order_id): is_status}
        redis_deal.hmset("strategy", strategy)
        db.session.delete(res)
        db.session.commit()
        response['response'] = res.damping_order_id
    else:
        response['status'] = 105
        response['response'] = 'null'
        response['msg'] = '未查询到该条数据'

    return response

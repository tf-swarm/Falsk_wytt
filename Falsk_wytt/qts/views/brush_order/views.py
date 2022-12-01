import datetime
import threading

from flask import request, session, current_app
from sqlalchemy import and_

from qts import db, constants
from qts.lib.check_login import login_check
from qts.lib.time_uuid import create_time_uuid
from . import brushOrder_blue
from qts.models import BrushOrder, Account
import json
from qts import redis_deal
from strategy.strategyManager import strategyManager
from qts.lib.power import get_page_power


@brushOrder_blue.route("/findPage", methods=['POST'])
@login_check
def find_page():
    response = {
        "status": 0,
        "error": None,
        "data": None,
        "msg": "suc"
    }
    exchange_list, bucket_list = [], []
    total = 0
    now_time = datetime.datetime.now()
    start_date = str(datetime.date(2020, 1, 1))
    end_date = str(now_time + datetime.timedelta(seconds=2))
    bucketing_id = request.json.get('bucketing_id')
    power_id = request.json.get('power_id')
    role_id = session.get('role_id')
    page = request.json.get('page')
    size = request.json.get('size')
    sort_ = request.json.get('sort')
    order = request.json.get('order')
    query = request.json.get('query')

    column_dict = {
        'bucketing_id': BrushOrder.bucketing_id.desc(),
        'created_date': BrushOrder.created_date.desc(),
        'updated_date': BrushOrder.updated_date.desc(),
        'user_id': BrushOrder.user_id.desc(),
    }
    if sort_ in column_dict.keys():
        pass
    else:
        sort_ = 'created_date'

    if bucketing_id:
        bucketing = BrushOrder.query.filter_by(bucketing_id=bucketing_id).first()
        bucket_info = bucketing.to_dict()
        json_info = json.loads(bucket_info.get("json_info"))
        bucket_id, create_time, is_enabled = bucket_info.get("id"), bucket_info.get("created_date"), bucket_info.get("is_enabled")
        amount = list(json_info.get("amount"))
        json_info.update({
            "id": bucket_id, "bucketing_id": bucket_id, "is_enabled": is_enabled, "created_date": create_time,
            "amount_start": amount[0], "amount_end": amount[1]
        })
        bucket_list.append(json_info)
        total = len(bucket_list)
    else:
        if query:
            user_id = query.get("userId")
            start_time = (query['startDate'] if "startDate" in query else start_date)
            end_time = (query['endDate'] if "endDate" in query else end_date)
            if order == "ASCE":
                bucket_data = BrushOrder.query.filter(and_(BrushOrder.user_id == user_id, BrushOrder.created_date >= start_time,
                                                          BrushOrder.created_date <= end_time)).order_by(sort_)
            else:
                bucket_data = BrushOrder.query.filter(
                    and_(BrushOrder.user_id == user_id, BrushOrder.created_date.__ge__(start_time),
                         BrushOrder.created_date.__le__(end_time))).order_by(column_dict[sort_])
            if bucket_data:
                p_age = bucket_data.paginate(page=page, per_page=size)
                total = p_age.total  # 查询返回的记录总数
                bucket_data = p_age.items
            for res in bucket_data:
                bucket_dict = res.to_dict()
                json_info = json.loads(bucket_dict.get("json_info"))
                bucket_id, create_time, is_enabled = bucket_dict.get("id"), bucket_dict.get("created_date"), bucket_dict.get("is_enabled")
                amount = list(json_info.get("amount"))
                json_info.update({
                    "id": bucket_id, "bucketing_id": bucket_id, "is_enabled": is_enabled, "created_date": create_time,
                    "amount_start": amount[0], "amount_end": amount[1]
                })
                bucket_list.append(json_info)
        else:
            response['error'] = '参数不全'

    if power_id:
        deal_power = get_page_power(role_id, power_id)
    else:
        deal_power = {}
    brush_info = {"total": total, "rows": bucket_list}
    response.update({"data": brush_info, "power": deal_power})
    print("--brushOrder--", response)
    return response


@brushOrder_blue.route("/save", methods=['POST'])
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
    bucketing_id = request.json.get('id')
    symbol = request.json.get('symbol')
    account_id = request.json.get('account_id')  # 下单账户ID
    account_name = request.json.get('account_name')
    max_wait = request.json.get('max_waitTime')
    min_wait = request.json.get('min_waitTime')
    base_amount = request.json.get('base_amount')
    amount_start = request.json.get('amount_start')
    amount_end = request.json.get('amount_end')
    quote_buffer = request.json.get('quote_buffer')
    day_rate = request.json.get('day_rate')
    pre_precision = request.json.get('price_precision')
    vol_precision = request.json.get('volume_precision')
    is_enabled = 0

    amount = [float(amount_start), float(amount_end)]
    result = Account.query.filter_by(account_id=account_id).first()
    if not result:
        response.update({"error": "账户不存在", "success": False, "status": 101})
    else:
        exchange = result.exchange
        bucket_info = {
            "exchange": exchange, "symbol": symbol, "account_id": account_id, "account_name": account_name, "amount": amount,
            "base_amount": float(base_amount), "quote_buffer": float(quote_buffer), "day_rate": float(day_rate),
            "max_waitTime": int(max_wait), "min_waitTime": int(min_wait),
            "price_precision": int(pre_precision), "volume_precision": int(vol_precision)
        }

        if bucketing_id:
            try:
                bucketing = BrushOrder.query.filter(BrushOrder.bucketing_id == bucketing_id).first()
                if bucketing:
                    bucketing.exchange = exchange
                    bucketing.symbol = symbol
                    bucketing.is_enabled = is_enabled
                    bucketing.json_info = json.dumps(bucket_info)
                    bucketing.created_date = bucketing.created_date
                    bucketing.updated_date = updated_date
                    bucketing.user_id = user_id

                    db.session.commit()

                    response['success'] = True
                    response['response'] = bucketing_id
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
            bucket_id = create_time_uuid()
            try:
                bucketing = BrushOrder(
                    bucketing_id=bucket_id,
                    exchange=exchange,
                    symbol=symbol,
                    is_enabled=is_enabled,
                    json_info=json.dumps(bucket_info),
                    created_date=created_date,
                    updated_date=updated_date,
                    user_id=user_id
                )

                db.session.add(bucketing)
                db.session.commit()

                response['success'] = True
                response['response'] = bucketing.bucketing_id
            except Exception as e:
                print(e)
                response['status'] = 101
                response['success'] = False
                response['error'] = e
            finally:
                response['timestamp'] = stamp
        print("--response--", response)
    return response


@brushOrder_blue.route("/start", methods=['GET'])
@login_check
def start():
    response = {
        'status': 0,
        'error': None,
        'data': None,
        'msg': 'suc'
    }
    bucketing_id = request.args.get('id')
    bucketing = BrushOrder.query.filter(BrushOrder.bucketing_id == bucketing_id).first()
    if bucketing:
        if bucketing.is_enabled == 0:
            is_status = 1
            bucketing.is_enabled = is_status
            json_info = json.loads(bucketing.json_info)
            account_id, account_name = json_info.get("account_id"), json_info.get("account_name")
            account = Account.query.filter(Account.account_id == account_id, Account.account_name == account_name).first()
            if account:
                account_info = account.to_dict()
                api_key, secret_key = account_info.get("api_key"), account_info.get("secret_key")
                json_info.update({"strategy_id": bucketing_id, "api_key": api_key, "secret_key": secret_key})

                strategy = {"{}".format(bucketing_id): is_status}
                redis_deal.hmset("strategy", strategy)
                print("--start_brushorder--", is_status, json_info)
                strategyManager.run("brushorder", json_info)
                db.session.commit()
                response['status'] = 0
                response['msg'] = '开启成功'
            else:
                response['status'] = 101
                response['msg'] = '下单账户异常'
        else:
            response['status'] = 102
            response['msg'] = '该对敲策略已开启'
    else:
        response['status'] = 104
        response['msg'] = '未知ID'

    return response


@brushOrder_blue.route("/stop", methods=['GET'])
@login_check
def stop():
    response = {
        'status': 0,
        'error': None,
        'data': None,
        'msg': 'suc'
    }
    bucketing_id = request.args.get('id')
    bucketing = BrushOrder.query.filter(BrushOrder.bucketing_id == bucketing_id).first()
    if bucketing:
        if bucketing.is_enabled == 1:
            is_status = 0
            bucketing.is_enabled = is_status
            strategy = {"{}".format(bucketing_id): is_status}
            redis_deal.hmset("strategy", strategy)
            print("--stop-", bucketing_id, is_status)
            db.session.commit()

            response['status'] = 0
            response['msg'] = '关闭成功'
        else:
            response['status'] = 103
            response['msg'] = '该对敲策略已关闭'
    else:
        response['status'] = 104
        response['msg'] = "未知ID"

    return response


@brushOrder_blue.route("/remove", methods=['GET'])
@login_check
def remove():
    response = {
        'status': 0,
        'error': None,
        'data': None,
        'msg': 'suc'
    }
    bucketing_id = request.args.get('id')
    res = BrushOrder.query.filter(BrushOrder.bucketing_id == bucketing_id).first()
    if res:
        is_status = 2
        strategy = {"{}".format(bucketing_id): is_status}
        redis_deal.hmset("strategy", strategy)
        db.session.delete(res)
        db.session.commit()
        response['response'] = res.bucketing_id
    else:
        response['status'] = 105
        response['response'] = 'null'
        response['msg'] = '未查询到该条数据'

    return response

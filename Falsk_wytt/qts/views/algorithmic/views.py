import datetime
import threading

from flask import request, session
from sqlalchemy import and_

from qts import db
from qts.lib.check_login import login_check
from qts.lib.time_uuid import create_time_uuid
from . import TWAP_blue
from qts.models import Account, TWAP
import json
from qts import redis_deal
from strategy.strategyManager import strategyManager
from qts.lib.power import get_page_power


@TWAP_blue.route("/findPage", methods=['POST'])
@login_check
def find_page():
    response = {
        "status": 0,
        "error": None,
        "data": None,
        "msg": "suc"
    }
    exchange_list, twap_list = [], []
    total = 0
    now_time = datetime.datetime.now()
    start_date = str(datetime.date(2020, 1, 1))
    end_date = str(now_time + datetime.timedelta(seconds=2))
    twap_id = request.json.get('twap_id')
    power_id = request.json.get('power_id')
    role_id = session.get('role_id')
    page = request.json.get('page')
    size = request.json.get('size')
    sort_ = request.json.get('sort')
    order = request.json.get('order')
    query = request.json.get('query')

    # column_dict = {
    #     'twap_id': TWAP.bucketing_id.desc(),
    #     'created_date': TWAP.created_date.desc(),
    #     'updated_date': TWAP.updated_date.desc(),
    #     'user_id': TWAP.user_id.desc(),
    # }
    # if sort_ in column_dict.keys():
    #     pass
    # else:
    #     sort_ = 'created_date'
    #
    # if twap_id:
    #     twap_weighted = TWAP.query.filter_by(twap_id=twap_id).first()
    #     weighted_info = twap_weighted.to_dict()
    #     json_info = json.loads(weighted_info.get("json_info"))
    #     weighted_id, create_time, is_enabled = weighted_info.get("id"), weighted_info.get("created_date"), weighted_info.get("is_enabled")
    #     amount = list(json_info.get("amount"))
    #     json_info.update({
    #         "id": weighted_id, "bucketing_id": weighted_id, "is_enabled": is_enabled, "created_date": create_time,
    #         "amount_start": amount[0], "amount_end": amount[1]
    #     })
    #     twap_list.append(json_info)
    #     total = len(twap_list)
    # else:
    #     if query:
    #         user_id = query.get("userId")
    #         start_time = (query['startDate'] if "startDate" in query else start_date)
    #         end_time = (query['endDate'] if "endDate" in query else end_date)
    #         if order == "ASCE":
    #             twap_data = TWAP.query.filter(and_(TWAP.user_id == user_id, TWAP.created_date >= start_time,
    #                                                       TWAP.created_date <= end_time)).order_by(sort_)
    #         else:
    #             twap_data = TWAP.query.filter(and_(TWAP.user_id == user_id, TWAP.created_date.__ge__(start_time),
    #                      TWAP.created_date.__le__(end_time))).order_by(column_dict[sort_])
    #         if twap_data:
    #             p_age = twap_data.paginate(page=page, per_page=size)
    #             total = p_age.total  # 查询返回的记录总数
    #             twap_data = p_age.items
    #         for res in twap_data:
    #             twap_dict = res.to_dict()
    #             json_info = json.loads(twap_dict.get("json_info"))
    #             bucket_id, create_time, is_enabled = twap_dict.get("id"), twap_dict.get("created_date"), twap_dict.get("is_enabled")
    #             amount = list(json_info.get("amount"))
    #             json_info.update({
    #                 "id": bucket_id, "bucketing_id": bucket_id, "is_enabled": is_enabled, "created_date": create_time,
    #                 "amount_start": amount[0], "amount_end": amount[1]
    #             })
    #             twap_list.append(json_info)
    #     else:
    #         response['error'] = '参数不全'
    #
    # exchange_list = get_exchange_info()
    #
    # response['data'] = {}
    # response["data"].update({
    #     "exchange": exchange_list, "total": total, "rows": twap_list
    # })

    if power_id:
        deal_power = get_page_power(role_id, power_id)
    else:
        deal_power = {}
    response.update({"power": deal_power})
    print("-twap_response--", response)
    return response


@TWAP_blue.route("/save", methods=['POST'])
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
    twap_id = request.json.get('id')
    account_id = request.json.get('account_id')  # 下单账户ID
    account_name = request.json.get('account_name')
    symbol = request.json.get('symbol')
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

    result = Account.query.filter_by(account_id=account_id).first()
    if not result:
        response.update({"error": "账户不存在", "success": False, "status": 101})
    else:
        exchange = result.exchange
        amount = [int(amount_start), int(amount_end)]
        bucket_info = {
            "exchange": exchange, "symbol": symbol, "account_id": account_id, "account_name": account_name, "amount": amount,
            "base_amount": int(base_amount), "quote_buffer": float(quote_buffer), "day_rate": float(day_rate),
            "max_waitTime": int(max_wait), "min_waitTime": int(min_wait),
            "price_precision": int(pre_precision), "volume_precision": int(vol_precision)
        }

        if twap_id:
            try:
                twap_info = TWAP.query.filter(TWAP.twap_id == twap_id).first()
                if twap_info:
                    twap_info.exchange = exchange
                    twap_info.symbol = symbol
                    twap_info.is_enabled = is_enabled
                    twap_info.json_info = json.dumps(bucket_info)
                    twap_info.created_date = twap_info.created_date
                    twap_info.updated_date = updated_date
                    twap_info.user_id = user_id
                    db.session.commit()
                    response['success'] = True
                    response['response'] = twap_id
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
            twap_id = create_time_uuid()
            try:
                twap_info = TWAP(
                    twap_id=twap_id,
                    exchange=exchange,
                    symbol=symbol,
                    is_enabled=is_enabled,
                    json_info=json.dumps(bucket_info),
                    created_date=created_date,
                    updated_date=updated_date,
                    user_id=user_id
                )

                db.session.add(twap_info)
                db.session.commit()

                response['success'] = True
                response['response'] = twap_info.bucketing_id
            except Exception as e:
                print(e)
                response['status'] = 101
                response['success'] = False
                response['error'] = e
            finally:
                response['timestamp'] = stamp
    return response


@TWAP_blue.route("/start", methods=['GET'])
@login_check
def start():
    response = {
        'status': 0,
        'error': None,
        'data': None,
        'msg': 'suc'
    }
    user_id = session.get('user_id')
    twap_id = request.args.get('id')
    twap_info = TWAP.query.filter(TWAP.twap_id == twap_id).first()
    if twap_info:
        if twap_info.is_enabled == 0:
            is_status = 1
            twap_info.is_enabled = is_status
            json_info = json.loads(twap_info.json_info)
            account_id, account_name = json_info.get("account_id"), json_info.get("account_name")
            account = Account.query.filter(Account.account_id == account_id, Account.account_name == account_name).first()
            if account:
                account_info = account.to_dict()
                api_key, secret_key = account_info.get("api_key"), account_info.get("secret_key")
                json_info.update({"strategy_id": twap_id, "api_key": api_key, "secret_key": secret_key})

                print("--start_TWAP--", is_status, json_info)
                strategy = {"{}".format(twap_id): is_status}
                redis_deal.hmset("strategy", strategy)
                strategyManager.run("twa", json_info)
                db.session.commit()
                response['status'] = 0
                response['msg'] = '开启成功'
            else:
                response['status'] = 101
                response['msg'] = '下单账户异常'
        else:
            response['status'] = 102
            response['msg'] = '该TWAP策略已开启'
    else:
        response['status'] = 104
        response['msg'] = '未知ID'

    return response


@TWAP_blue.route("/stop", methods=['GET'])
@login_check
def stop():
    response = {
        'status': 0,
        'error': None,
        'data': None,
        'msg': 'suc'
    }
    twap_id = request.args.get('id')
    twap_info = TWAP.query.filter(TWAP.twap_id == twap_id).first()
    if twap_info:
        if twap_info.is_enabled == 1:
            is_status = 0
            twap_info.is_enabled = is_status
            strategy = {"{}".format(twap_id): is_status}
            redis_deal.hmset("strategy", strategy)
            db.session.commit()

            response['status'] = 0
            response['msg'] = '关闭成功'
        else:
            response['status'] = 103
            response['msg'] = '该TWAP策略已关闭'
    else:
        response['status'] = 104
        response['msg'] = "未知ID"

    return response


@TWAP_blue.route("/remove", methods=['GET'])
@login_check
def remove():
    response = {
        'status': 0,
        'error': None,
        'data': None,
        'msg': 'suc'
    }
    twap_id = request.args.get('id')
    res = TWAP.query.filter(TWAP.twap_id == twap_id).first()
    if res:
        is_status = 2
        strategy = {"{}".format(twap_id): is_status}
        redis_deal.hmset("strategy", strategy)
        db.session.delete(res)
        db.session.commit()
        response['response'] = res.twap_id
    else:
        response['status'] = 105
        response['response'] = 'null'
        response['msg'] = '未查询到该条数据'
    return response

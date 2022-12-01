from flask import request, session
from qts.lib.check_login import login_check
from . import analyze_blue
from qts.models import Account, BalanceCount, TradesRecord, CoinHistory
from qts.utils.tool.tool import Time
from datetime import datetime, date, timedelta
from qts.lib.power import get_account_list, paging
import json
import numpy as np


@analyze_blue.route("/trades_info", methods=['POST'])
@login_check
def trades_page():

    response = {
        "status": 0,
        "error": None,
        "data": None,
        "msg": "suc"
    }
    pages = request.json.get('page')
    size = request.json.get('size')
    query = request.json.get('query')
    user_id = session.get('user_id')
    account_list = get_account_list(user_id)

    if "startDate" in query and "endDate" in query:
        start_time, end_time = query.get("startDate"), query.get("endDate")
        start_date, end_date = start_time + " 00:00:00", end_time + " 23:59:59"
        if query.get("accountName") and query.get("symbol"):
            account_id = query.get("accountId")
            symbol = query.get("symbol").replace("/", "")
            record_list = TradesRecord.query.filter(TradesRecord.insert_date.between(start_date, end_date),
                                                    TradesRecord.account_id == account_id, TradesRecord.symbol == symbol)
        elif query.get("accountName") and not query.get("symbol"):
            account_id = query.get("accountId")
            record_list = TradesRecord.query.filter(TradesRecord.insert_date.between(start_date, end_date),
                                                    TradesRecord.account_id == account_id)
        elif not query.get("accountName") and query.get("symbol"):
            symbol = query.get("symbol").replace("/", "")
            record_list = TradesRecord.query.filter(TradesRecord.insert_date.between(start_date, end_date),
                                                    TradesRecord.symbol == symbol)
        else:
            record_list = TradesRecord.query.filter(TradesRecord.insert_date.between(start_date, end_date), TradesRecord.account_id.in_(account_list))
    elif "startDate" not in query and "endDate" not in query:
        day_time = datetime.now().strftime('%Y-%m-%d')
        month_time = (date.today() + timedelta(days=-30)).strftime("%Y-%m-%d")
        start_date, end_date = month_time + " 00:00:00", day_time + " 23:59:59"
        if query.get("accountName") and not query.get("symbol"):
            account_id = query.get("accountId")
            symbol = query.get("symbol").replace("/", "")
            record_list = TradesRecord.query.filter(TradesRecord.insert_date.between(start_date, end_date),
                                                    TradesRecord.account_id == account_id, TradesRecord.symbol == symbol)
        elif not query.get("accountName") and query.get("symbol"):
            symbol = query.get("symbol").replace("/", "")
            record_list = TradesRecord.query.filter(TradesRecord.insert_date.between(start_date, end_date),
                                                    TradesRecord.symbol == symbol)
        elif query.get("accountName") and not query.get("symbol"):
            account_id = query.get("accountId")
            record_list = TradesRecord.query.filter(TradesRecord.insert_date.between(start_date, end_date),
                                                    TradesRecord.account_id == account_id)
        else:
            record_list = TradesRecord.query.filter(TradesRecord.insert_date.between(start_date, end_date), TradesRecord.account_id.in_(account_list))
    else:
        response.update({"msg": "fail", "error": "参数错误", "status": 401})
        return response

    deal_list = []
    for info in record_list:
        trades = info.to_dict()
        result = json.loads(trades["json_info"])
        date_time, account_name = trades.get("insert_date", 0), trades.get("account_name", 0)
        symbol, order_id = result.get("symbol", 0), result.get("orderId", 0)
        status, price = ("买" if result.get("is_buyer", 0) else "卖"), float(result.get("price", 0))
        # status, price = result.get("is_buyer", 0), float(result.get("price", 0))
        qty, commission, asset = round(float(result.get("qty", 0)), 2), float(result.get("commission", 0)), result.get("commissionAsset", 0)
        deal_info = {
            "date": date_time, "account_name": account_name, "symbol": symbol, "order_id": order_id,
            "status": status, "price": price, "qty": qty, "commission": commission, "asset": asset
            }
        deal_list.append(deal_info)
    total, rows_list = paging(pages, size, deal_list)
    response['data'] = {}
    response["data"].update({"rows": rows_list, "total": total})
    return response


@analyze_blue.route("/balance_count", methods=['GET'])
@login_check
def balance_count():
    """账户余额统计"""
    response = {
        "status": 0,
        "error": None,
        "data": None,
        "msg": "suc"
    }

    pages = int(request.args.get('page'))
    size = int(request.args.get('size'))
    query = eval(request.args.get('query'))
    user_id = session.get('user_id')
    header_list = [
        {"label": "日期", "prop": "date", "min": "180"},
        {"label": "账户名称", "prop": "account_name", "min": "180"}
        ]
    symbol_list, rows_list, deal_list = [], [], []
    account_list = get_account_list(user_id)

    if "startDate" in query and "endDate" in query:
        start_time, end_time = query.get("startDate"), query.get("endDate")
        start_date, end_date = start_time + " 00:00:00", end_time + " 23:59:59"
        if query.get("accountName"):
            account_id = query.get("accountId")
            record_list = BalanceCount.query.filter(BalanceCount.insert_date.between(start_date, end_date),BalanceCount.account_id == account_id)
        else:
            record_list = BalanceCount.query.filter(BalanceCount.insert_date.between(start_date, end_date), BalanceCount.account_id.in_(account_list)).all()

    elif "startDate" not in query and "endDate" not in query:
        day_time = datetime.now().strftime('%Y-%m-%d')
        month_time = (date.today() + timedelta(days=-30)).strftime("%Y-%m-%d")
        start_date, end_date = month_time + " 00:00:00", day_time + " 23:59:59"
        if query.get("accountName"):
            account_id = query.get("accountId")
            record_list = BalanceCount.query.filter(BalanceCount.insert_date.between(start_date, end_date), BalanceCount.account_id == account_id)
        else:
            record_list = BalanceCount.query.filter(BalanceCount.insert_date.between(start_date, end_date), BalanceCount.account_id.in_(account_list)).all()
    else:
        response.update({"msg": "fail", "error": "参数错误", "status": 401})
        return response

    for info in record_list:
        balance = info.to_dict()
        rows_info = {"date": balance["insert_date"], "account_name": balance["account_name"]}
        asset_list = json.loads(balance["json_info"])
        for data in asset_list:
            asset = data["asset"]
            if asset not in symbol_list:
                symbol_list.append(asset)
                header_info = {"label": "{}".format(asset), "prop": "{}".format(asset), "min": "180"}
                header_list.append(header_info)
            rows_info[asset] = data["free"]
        rows_list.append(rows_info)
    for rows in rows_list:
        for symbol in symbol_list:
            if symbol not in rows:
                rows[symbol] = 0
            else:
                continue
        deal_list.append(rows)
    total, rows_list = paging(pages, size, deal_list)
    response['data'] = {}
    response["data"].update({
        "header_list": header_list, "rows_list": rows_list, "total": total
    })
    return response


@analyze_blue.route("/balance_reports", methods=['POST'])
@login_check
def balance_analyze():
    """账户余额分析"""
    response = {
        "status": 0,
        "error": None,
        "data": None,
        "msg": "suc"
    }
    query = request.json.get('query')
    user_id = session.get('user_id')
    legend_list = []
    account_list = get_account_list(user_id)
    for account_id in account_list:
        res = Account.query.filter_by(account_id=account_id).first()
        legend_list.append(res.account_name)

    if "startDate" in query and "endDate" in query:
        start_time, end_time = query.get("startDate"), query.get("endDate")
        start_date, end_date = start_time + " 00:00:00", end_time + " 23:59:59"
        record_list = BalanceCount.query.filter(BalanceCount.insert_date.between(start_date, end_date), BalanceCount.account_id.in_(account_list)).all()
    elif "startDate" not in query and "endDate" not in query:
        day_time = datetime.now().strftime('%Y-%m-%d')
        month_time = (date.today() + timedelta(days=-5)).strftime("%Y-%m-%d")
        start_date, end_date = month_time + " 00:00:00", day_time + " 23:59:59"
        record_list = BalanceCount.query.filter(BalanceCount.insert_date.between(start_date, end_date), BalanceCount.account_id.in_(account_list)).all()
    else:
        response.update({"msg": "fail", "error": "参数错误", "status": 401})
        return response

    series_info, x_axis_list, temp_list = {}, [], []
    zero = 0
    for info in record_list:
        balance = info.to_dict()
        account_name = balance["account_name"]
        date_time = balance["insert_date"]
        if account_name not in series_info:
            series_info[account_name] = []
        if date_time[:16] not in temp_list:
            temp_list.append(date_time[:16])
            x_axis_list.append(date_time)
        dollar_num = 0
        asset_list = json.loads(balance["json_info"])
        for data in asset_list:
            num = float(data["free"]) + float(data["locked"])
            number = num * float(data["price"])
            dollar_num = round(dollar_num + number, 2)
        zero = zero + 1
        series_info[account_name].append(dollar_num)

    for s in legend_list:
        if s not in series_info:
            series_info[s] = [0]*zero
        else:
            continue
    series_list, sum_list = [], []
    if series_info:
        legend_list.append("合计")
        for legend in legend_list:
            legend_info = {"type": "line", "stack": "总量", "areaStyle": {"normal": {}}}
            if legend == "合计":
                new_list = list(np.sum(sum_list, axis=0))
                legend_info.update({"name": legend, "data": new_list})
            else:
                data_info = series_info.get(legend, "")
                legend_info.update({"name": legend, "data": data_info})
                sum_list.append(data_info)
            series_list.append(legend_info)
    reports_info = {"legend": legend_list, "series": series_list, "xAxis": x_axis_list}
    response['data'] = {}
    response["data"].update(reports_info)
    return response


@analyze_blue.route("/transfer_info", methods=['POST'])
@login_check
def transfer_record():
    """充提币记录"""
    response = {
        "status": 0,
        "error": None,
        "data": None,
        "msg": "suc"
    }
    pages = request.json.get('page')
    size = request.json.get('size')
    query = request.json.get('query')
    user_id = session.get('user_id')
    print("--transfer--", request.json)
    account_list = get_account_list(user_id)

    if "startDate" in query and "endDate" in query:
        start_time, end_time = query.get("startDate"), query.get("endDate")
        start_date, end_date = start_time + " 00:00:00", end_time + " 23:59:59"
        if query.get("accountName"):
            account_id = query.get("accountId")
            deposit_list = CoinHistory.query.filter(CoinHistory.insert_date.between(start_date, end_date), CoinHistory.account_id == account_id)
        else:
            deposit_list = CoinHistory.query.filter(CoinHistory.insert_date.between(start_date, end_date), CoinHistory.account_id.in_(account_list)).all()

    elif "startDate" not in query and "endDate" not in query:
        day_time = datetime.now().strftime('%Y-%m-%d')
        month_time = (date.today() + timedelta(days=-30)).strftime("%Y-%m-%d")
        start_date, end_date = month_time + " 00:00:00", day_time + " 23:59:59"
        if query.get("accountName"):
            account_id = query.get("accountId")
            deposit_list = CoinHistory.query.filter(CoinHistory.insert_date.between(start_date, end_date), CoinHistory.account_id == account_id)
        else:
            deposit_list = CoinHistory.query.filter(CoinHistory.insert_date.between(start_date, end_date), CoinHistory.account_id.in_(account_list)).all()
    else:
        response.update({"msg": "fail", "error": "参数错误", "status": 401})
        return response

    deal_list = []
    for info in deposit_list:
        deposit = info.to_dict()
        result = json.loads(deposit["json_info"])
        result.update({"date": deposit["insert_date"], "type": ("转入" if deposit["transfer_type"] == 1 else "转出")})
        deal_list.append(result)
    total, rows_list = paging(pages, size, deal_list)
    response['data'] = {}
    response["data"].update({"rows": rows_list, "total": total})
    return response


@analyze_blue.route("/balance_rate", methods=['GET', 'POST'])
@login_check
def rate_info():
    """账户余额占比"""
    response = {
        "status": 0,
        "error": None,
        "data": None,
        "msg": "suc"
    }

    ts = Time.timestamp_to_str(Time.current_ts())
    # ts = '2021-09-17 15:36:47'
    user_id = session.get('user_id')
    account_list = get_account_list(user_id)
    user_list, rate_list = [], []
    accounts_list, series_list, symbol_list = [], [], []
    for account_id in account_list:
        res = Account.query.filter_by(account_id=account_id).first()
        account_info = {"Id": account_id, "account": res.account_name}
        user_list.append(account_info)
    if request.method == 'GET':
        check_list, symbol_list = account_list, []
    else:
        # {'query': {'userId': 1, 'date_time': '2021-09-15 14:39:02'}, 'check_list': '1,2,3,4'}
        date_time = request.json.get('query').get("date_time", 0)
        check_str = request.json.get('check_list')
        if date_time and check_str:
            ts, check_list = date_time, [int(s) for s in check_str.split(",")]
        else:
            response.update({"msg": "fail", "error": "参数错误", "status": 401})
            return response
    start_date = Time.timestamp_to_str(Time.str_to_timestamp(ts) - 6 * 60 * 60)
    end_date = ts
    record_list = BalanceCount.query.filter(BalanceCount.insert_date.between(start_date, end_date), BalanceCount.account_id.in_(check_list)).all()
    for data in record_list:
        balance_info = {}
        balance = data.to_dict()
        account_id, account_name = balance["account_id"], balance["account_name"]
        json_info = json.loads(balance["json_info"])
        for info in json_info:
            asset, free, locked, price = info["asset"], info["free"], info["locked"], info["price"]
            number = round(float(free) + float(locked), 2)
            balance_info[asset] = {"number": number, "price": price}
            if asset not in symbol_list:
                symbol_list.append(asset)
            else:
                continue
        accounts_info = {"field": "account{}".format(account_id), "name": account_name, "balance": balance_info}
        accounts_list.append(accounts_info)
    for symbol in symbol_list:
        sum_number, sum_count, prices = 0, 0, 0
        t_info = {"symbol": symbol}
        for account in accounts_list:
            field = account["field"]
            if symbol in account["balance"]:
                prices = account["balance"][symbol]["price"]
                count = account["balance"][symbol]["number"]
            else:
                count = 0
            t_info["{}".format(field)] = count
            sum_number += count
        sum_count = round(sum_number * prices, 2)
        t_info.update({"sumNumber": round(sum_number, 2), "sumCount": sum_count})
        s_info = {"value": sum_count, "name": symbol}
        series_list.append(s_info)
        rate_list.append(t_info)
    data_info = {"user": user_list, "check_user": check_list, "ts": ts, "symbol": symbol_list,
                 "series": series_list, "accounts": accounts_list, "rate": rate_list}
    response.update({"data": data_info})
    return response


@analyze_blue.route("/balance_change", methods=['GET', 'POST'])
@login_check
def change_info():
    """账户余额涨幅"""
    response = {
        "status": 0,
        "error": None,
        "data": None,
        "msg": "suc"
    }
    user_id = session.get('user_id')
    now_time = Time.current_time('%Y-%m-%d')
    account_list = get_account_list(user_id)
    user_list, as_list, axis_list = [], [], []
    accounts_list, series_list, symbol_list = [], [], []
    aid_list, axis_data, rows_list = [], {}, []
    for account_id in account_list:
        res = Account.query.filter_by(account_id=account_id).first()
        account_info = {"Id": account_id, "account": res.account_name}
        user_list.append(account_info)
    if request.method == 'GET':
        now_time = "2021-09-24"
        check_list = account_list
        start_date, end_date = now_time + " 00:00:00", now_time + " 23:59:59"

    else:
        query = request.json.get('query')
        start_time, end_time = query.get("start", 0), query.get("end", 0)
        check_str = request.json.get('check_list')
        if start_time and end_time and check_str:
            start_date, end_date = start_time, end_time
            check_list = [int(s) for s in check_str.split(",")]
        else:
            response.update({"msg": "fail", "error": "参数错误", "status": 401})
            return response

    balance_list = BalanceCount.query.filter(BalanceCount.insert_date.between(start_date, end_date),BalanceCount.account_id.in_(check_list)).all()
    for data in balance_list:
        balance_info = {}
        balance = data.to_dict()
        insert_time = balance["insert_date"]
        account_id, account_name = balance["account_id"], balance["account_name"]
        json_info = json.loads(balance["json_info"])
        if account_id not in as_list:
            accounts_info = {"field": "account{}".format(account_id), "name": account_name, "balance": balance_info}
            accounts_list.append(accounts_info)
            as_list.append(account_id)
        for info in json_info:
            asset, free, locked, price = info["asset"], info["free"], info["locked"], info["price"]
            number = round(float(free) + float(locked), 2)
            balance_info[asset] = {"number": number, "price": price}

            if asset not in symbol_list:
                symbol_list.append(asset)
            else:
                continue

        if insert_time not in axis_data:
            axis_data[insert_time] = []
        axis_info = {"field": "account{}".format(account_id), "name": account_name, "balance": balance_info}
        axis_data[insert_time].append(axis_info)

    deal_list = []
    for keys, values in axis_data.items():
        series_info = {}
        for data in values:
            for key, value in data["balance"].items():
                if key not in series_info:
                    series_info[key] = round(float(value["number"] * value["price"]), 2)
                else:
                    series_info[key] = round(series_info[key] + float(value["number"] * value["price"]), 2)
        deal_list.append(series_info)

    for keys, acc_list in axis_data.items():
        for symbol in symbol_list:
            sum_number, sum_count, prices = 0, 0, 0
            t_info = {"date": keys, "symbol": symbol}
            for account in acc_list:
                field = account["field"]
                if symbol in account["balance"]:
                    prices = account["balance"][symbol]["price"]
                    count = account["balance"][symbol]["number"]
                else:
                    count = 0
                t_info["{}".format(field)] = count
                sum_number += count
            sum_count = round(sum_number * prices, 2)
            t_info.update({"sumNumber": round(sum_number, 2), "sumCount": sum_count})
            rows_list.append(t_info)
        axis_list.append(keys)

    deal_info = {}
    for deal in deal_list:
        for key, value in deal.items():
            if key not in deal_info:
                deal_info[key] = []
                deal_info[key].append(value)
            else:
                deal_info[key].append(value)
    for keys, values in deal_info.items():
        s = {"name": keys, "type": "line", "stack": "总量", "data": values}
        series_list.append(s)

    data_info = {"start": start_date, "end": end_date, "user": user_list, "check_user": check_list, "accounts": accounts_list,
                 "symbol": symbol_list, "axis": axis_list, "rows": rows_list, "series": series_list}
    response.update({"data": data_info})
    return response
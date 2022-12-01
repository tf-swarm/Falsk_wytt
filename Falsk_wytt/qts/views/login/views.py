import base64
import os
import re

from flask import request, jsonify, session, current_app
from qts.lib.crypto_demo import CryptoRsa
from qts import redis_store
from qts.models import User, PermissionApi, Role, Account, Exchange
from . import login_blue
from qts.constants import USERS
from qts.lib.power import get_auth_fn


@login_blue.route("/key", methods=["GET"])
def public_key():
    path = os.path.dirname(__file__).split('qts')[0]
    with open(path + "rsa_public_key.pem", "rb") as x:
        f = x.read()
    bs = base64.b64encode(f)
    return jsonify({'pem': bs.decode()})


@login_blue.route("/login", methods=["POST"])
def login():
    username = request.json.get("username")
    ciphertext = request.json.get("password")
    img_code = request.json.get("img_code")
    uuid = request.json.get("uuid")
    if not all([username, ciphertext, img_code, uuid]):
        return jsonify(success=False, error="参数错误")
    match = re.match(r"^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$", uuid)
    if not match:
        return jsonify(success=False, error="uuid错误")
    user = User.query.filter(User.name == username).first()
    real_img_code = redis_store.get("ImageCode_" + uuid)
    redis_store.delete("ImageCode_" + uuid)
    if not real_img_code:
        return jsonify(success=False, error="图片验证码过期")
    if real_img_code.upper() != img_code.upper():
        return jsonify(success=False, error="图片验证码错误")
    if not user:
        return jsonify(success=False, error="用户不存在")
    path = os.path.dirname(__file__).split('qts')[0]

    password = CryptoRsa(password='quant2021').rsa_decrypto(ciphertext=ciphertext, path=path)

    result = user.check_password(user, password)
    if not result:
        return jsonify(success=False, error="密码错误")
    user_id = user.user_id

    session["user_id"] = user_id
    session["role_id"] = user.role_id
    session["name"] = user.name
    try:
        volume_precision = USERS[user_id]['volume_precision']
        price_precision = USERS[user_id]['price_precision']
        min_order_volume = USERS[user_id]['min_order_volume']
    except Exception as e:
        print(e)
        current_app.logger.error(e)
        return jsonify(success=False, error="获取不到精度")
    else:
        role_id = str(user.role_id)
        if role_id == "0":
            account_list = Account.query.all()
        else:
            account_list = []
            if user.account_ids:
                aid_list = user.account_ids.split(",")
                for aid in aid_list:
                    result_account = Account.query.filter_by(account_id=aid).first()
                    account_list.append(result_account)

        res_info = Exchange.query.all()
        account_info = []
        for account in account_list:
            index = account.account_id
            exchange = account.exchange
            res_symbol, exchange_list = [], []
            for res_one in res_info:
                symbol_result = {}
                exchange_name = res_one.exchange_name
                symbol_id = res_one.ex_id
                if exchange == exchange_name:
                    exchange_list.append(symbol_id)
                if str(res_one.exchange_level) == "1":
                    if role_id == "0" and res_one.exchange_id in exchange_list:
                        symbol_result.update({
                            "id": symbol_id, "Name": exchange_name,
                        })
                        res_symbol.append(symbol_result)
                    else:
                        symbol_list = account.symbol_ids.split(",")
                        if str(symbol_id) not in symbol_list:
                            continue
                        else:
                            symbol_result.update({
                                "id": symbol_id, "Name": exchange_name,
                            })
                            res_symbol.append(symbol_result)
            account_info.append({
                "id": index,
                "Name": account.account_name,
                "exchange": exchange,
                "symbol": res_symbol,
            })

        symbol_list, symbol, ac_name, account_id = [], "", "", ""
        if len(account_info) > 0:
            res_account = account_info[0]
            symbol_list = res_account["symbol"]
            if symbol_list:
                symbol, ac_name, account_id = symbol_list[0]["Name"], res_account["Name"], res_account["id"]

        user_info = {
            "user_id": user_id,
            "accountId": account_id,
            "user_name": user.name,
            "account_list": account_info,
            "symbol_list": symbol_list,
            "accountName": ac_name,
            "symbol": symbol,
            "volume_precision": volume_precision,
            "price_precision": price_precision,
            "min_order_volume": min_order_volume,
        }
        return jsonify(status=0, msg='suc', error=None, data=user_info)


@login_blue.route("/menu_list", methods=["POST"])
def get_menu_data():
    response = {
        "status": 0,
        "error": None,
        "data": None,
        "msg": "suc"
    }
    user_name = request.json.get("userName")
    res = User.query.filter(User.name == user_name).first()
    if res:
        api_list = PermissionApi.query.all()
        role_id = res.role_id
        print("--menu_list--:", role_id)
        if role_id == 0:
            result_info = get_auth_fn(role_id, None, api_list)
            response.update({"data": result_info})
        else:
            result = Role.query.filter(Role.role_id == role_id).first()
            if result:
                key_role_perms = {}
                role_perms = result.ps_ids.split(",")
                for role_perm in role_perms:
                    key_role_perms[int(role_perm)] = True
                result_info = get_auth_fn(role_id, key_role_perms, api_list)
                response.update({"data": result_info})
            else:
                response.update({"data": []})
    else:
        response.update({"msg": "fail", "error": "未获取到用户信息", "status": 401})
    return jsonify(response)


@login_blue.route("/logout")
def logout():
    session.pop('user_id', None)
    session.pop('name', None)
    session.pop('role_id', None)
    return jsonify(success=True, error="成功退出")


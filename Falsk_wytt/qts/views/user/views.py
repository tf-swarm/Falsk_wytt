import datetime
import re

from flask import request, jsonify, session, current_app

from qts import db
from qts.lib.accounts import user_util
from qts.lib.check_login import login_check
from qts.models import User, Account, Role
from qts.views.user import user_blue
from qts.lib.power import get_page_power


@user_blue.route("/register", methods=["POST"])
def register():
    response = {
        'status': 0,
        'error': None,
        'data': None,
        'msg': 'suc'
    }
    user_name = request.json.get('name')
    password = request.json.get('password')
    mobile = request.json.get('mobile')
    email = request.json.get('email')
    # authorization_code = request.json.get('authorizationCode')
    salt, state = 'e10adc3949ba59abbe56e057f20f883e', 1

    result = User.query.filter(User.name == user_name).first()
    if not result:
        now_date = datetime.datetime.now()
        num_letter = re.compile("^(?!\d+$)[\da-zA-Z_]+$")
        # WYQT-IO3Q-GNUO-53LB
        # if authorization_code != '2JP9-YOVO-R98X-2AKU':
        #     response.update({"msg": "无效授权码", "status": 1})
        if num_letter.search(user_name):
            user = User(name=user_name, password=password, salt=salt, mobile=mobile,
                        email=email, state=state, account_ids="", create_date=now_date
                        )
            db.session.add(user)
            db.session.commit()
            user_util(user.to_dict())

            response.update({"msg": "注册成功", "data": user.to_dict()})
        else:
            response.update({"msg": "用户名不合法", "status": 1})
    else:
        response.update({"msg": "用户名已存在", "status": 1})
    print("--register--", response)
    return jsonify(response)


@user_blue.route("/changePassword", methods=["POST"])
@login_check
def change_password():
    """
    {"oldPassword":"123456","newPassword":"456789","password":"456789"}
    :return:
    """
    response = {
        'status': 0,
        'error': None,
        'data': None,
        'msg': 'suc'
    }

    user_id = session.get('user_id')
    old_password = request.json.get('oldPassword')
    new_password = request.json.get('newPassword')
    password = request.json.get('password')
    if not all([old_password, new_password, password]):
        response.update({"status": 1, "msg": "fail", "error": "参数不足"})
        return response
    if new_password != password:
        response.update({"status": 1, "msg": "fail", "error": "两次密码不一致"})
        return response
    user = User.query.filter(User.user_id == user_id).first()
    if user.password != old_password:
        response.update({"status": 1, "msg": "fail", "error": "原密码有误"})
        return response
    user.password = new_password
    db.session.commit()
    return response


@user_blue.route("/user", methods=["POST"])
@login_check
def get_users():
    response = {
        "status": 0,
        "error": None,
        "data": None,
        "msg": "suc"
    }

    page = request.json.get('page')
    size = request.json.get('size')
    query = request.json.get('query')
    power_id = request.json.get('power_id')
    role_id = session.get('role_id')

    user_list = []
    if query == "":
        users = User.query.order_by("user_id")
    else:
        users = User.query.filter(User.name.contains(query)).order_by("user_id")
    p = users.paginate(page=page, per_page=size)
    total = p.total  # 查询返回的记录总数
    res_list = p.items
    for user in res_list:
        aid_list = user.account_ids.split(",")
        role = Role.query.filter(Role.role_id == user.role_id).first()
        if role:
            role_name = role.role_name
        else:
            role_name = ("VIP管理员" if user.role_id == 0 else "普通用户")
        state = (True if user.state == 1 else False)
        # 获取账户ID数据
        children = []
        for index, aid in enumerate(aid_list):
            if aid != "":
                res_info = Account.query.filter_by(account_id=aid).first()
                account_id = res_info.account_id
                children.append(account_id)
            else:
                continue
        user_info = {"id": user.user_id, "role_name": role_name, "username": user.name,
                     "state": state, "mobile": user.mobile, "email": user.email,
                     "children": children, "create_time": user.create_date
                     }
        user_list.append(user_info)

    rows_info = {"total": total, "rows": user_list}
    if power_id:
        deal_power = get_page_power(role_id, power_id)
    else:
        deal_power = {}
    response.update({"data": rows_info, "power": deal_power})
    return response


@user_blue.route("/state", methods=["GET"])
@login_check
def update_active():
    """修改用户登陆状态"""
    response = {
        "status": 0,
        "error": None,
        "data": None,
        "msg": "suc"
    }
    user_id = request.args.get('id')
    state = request.args.get('state')
    res = User.query.filter(User.user_id == user_id).first()
    if res.role_id != 0:
        if state == "true":
            res.state = 1
        else:
            res.state = 0
        db.session.commit()
        response['data'] = {
            "id": res.user_id, "rid": res.role_id,
            "state": res.state, "mobile": res.mobile,
            "email": res.email, "username": res.name
        }
        response.update({"msg": "状态修改成功"})
    else:
        response.update({"msg": "fail", "error": "无权限访问", "status": 404})
    return response


@user_blue.route("/adduser", methods=["POST"])
@login_check
def create_user():
    """添加用户"""
    response = {
        "status": 0,
        "error": None,
        "data": None,
        "msg": "suc"
    }

    username = request.json.get('username')
    salt = 'e10adc3949ba59abbe56e057f20f883e'

    res = User.query.filter(User.name == username).first()
    if res:
        response.update({"status": 404, "msg": "fail", "error": "用户名已存在"})
    else:
        password = request.json.get('password')
        email = request.json.get('email')
        mobile = request.json.get('mobile')
        now_date, state = datetime.datetime.now(), 1
        user = User(name=username, password=password, salt=salt,
                    mobile=mobile, email=email, state=state,
                    account_ids="", create_date=now_date)
        db.session.add(user)
        db.session.commit()
        # 设置精度
        user_util(user.to_dict())
        response.update({"msg": "用户创建成功", "data": user.to_dict()})
    return response


@user_blue.route("/users_Id", methods=["GET"])
@login_check
def deal_users():
    """state:1.根据id查询用户 2.更新用户 3.删除用户"""
    response = {
        "status": 0,
        "error": None,
        "data": None,
        "msg": "suc"
    }
    mg_id = request.args.get('id')
    state_id = request.args.get('state')
    if state_id == "1":
        res = User.query.filter(User.user_id == mg_id).first()
        user_info = {"id": res.user_id, "username": res.name, "mobile": res.mobile,
                     "email": res.email, "role_id": res.role_id
                     }
        response["data"] = user_info
    if state_id == "2":
        email = request.args.get('email')
        mobile = request.args.get('mobile')
        result = User.query.filter(User.user_id == mg_id).first()
        result.mobile = mobile
        result.email = email
        db.session.commit()
        user_info = {"id": result.user_id, "username": result.name, "mobile": result.mobile,
                     "email": result.email, "role_id": result.role_id
                     }
        response["data"] = user_info
    if state_id == "3":
        res_user = User.query.filter(User.user_id == mg_id).first()
        if str(res_user.role_id) == "0":
            response.update({"msg": "fail", "error": "无权限删除", "status": 404})
        else:
            User.query.filter(User.user_id == mg_id).delete()
            db.session.commit()
    return response


@user_blue.route("/set_role", methods=["GET"])
@login_check
def set_user_role():
    """分配用户角色"""
    response = {
        "status": 0,
        "error": None,
        "data": None,
        "msg": "suc"
    }
    user_id = request.args.get('user_id')
    role_id = request.args.get('role_id')
    result = User.query.filter(User.user_id == user_id).first()
    if not result.role_id:
        result.role_id = role_id
        db.session.commit()
        data_info = {
            "id": result.user_id,
            "rid": role_id,
            "username": result.name,
            "mobile": result.mobile,
            "email": result.email
        }
    else:
        if int(result.role_id) != 0:
            result.role_id = role_id
            db.session.commit()
            data_info = {
                "id": result.user_id,
                "rid": role_id,
                "username": result.name,
                "mobile": result.mobile,
                "email": result.email
            }
        else:
            data_info = {"msg": "fail", "error": "无权限访问", "status": 404}
    response.update({"data": data_info})
    return response


@user_blue.route("/deal_account", methods=["GET", "POST"])
@login_check
def get_allot_account():
    """对账户进行分配"""
    response = {
        "status": 0,
        "error": None,
        "data": None,
        "msg": "suc"
    }
    if request.method == "GET":
        result_list = []
        res = Account.query.all()
        for account in res:
            result_info = {}
            account_info = account.to_dict()
            result_info.update({
                "Id": account_info["id"],
                "Name": account_info["account_name"],
            })
            result_list.append(result_info)
            response.update({"data": result_list})
    else:
        user_id = request.json.get('userId')
        account_str = request.json.get('aids')
        res = User.query.filter(User.user_id == user_id).first()
        res.account_ids = account_str
        try:
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            response.update({"error": "修改失败", "status": 1, "success": False})
    return response

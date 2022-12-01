# coding:utf-8
from flask import jsonify, request, abort, current_app, make_response

from qts import redis_store, constants
from qts.lib.captcha_image import captcha, ImageCode
from qts.views.inspect import index_blue


@index_blue.route('/', methods=['GET'])
def home():
    return '系统首页'


@index_blue.route('/json', methods=['GET'])
def index():
    response = {
        'status': 0,
        'error': None,
        'data': None,
        'msg': 'suc'
    }
    return jsonify(response)


@index_blue.route("/imageCode", methods=['GET'])
def generate_image_code():
    """图片验证码"""
    # 获取图片验证码的UUID即code_id
    image_code_id = request.args.get("uuid")

    if not image_code_id:
        abort(403)

    # 生成图片验证码，其返回为名字、文本、以及图片
    # name, text, image = captcha.generate_captcha()
    text, images = ImageCode.get_verify_code()

    print("图片验证码是：{}".format(text))

    # 将图形验证码保存到redis数据库中
    try:
        # 保存当前生成的图片验证码内容，并且设置过期时间
        redis_store.setex('ImageCode_' + image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        current_app.logger.error(e)

    response = make_response(images)

    # 设置请求头属性-Content-Type响应的格式
    response.headers["Content-Type"] = "image/png"

    return response

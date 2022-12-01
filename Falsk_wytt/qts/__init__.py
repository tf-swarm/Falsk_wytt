import os

import redis
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session

import logging
from logging.handlers import TimedRotatingFileHandler

from qts.lib.thraed_control import start_thread
from config import config_map

db = SQLAlchemy()

redis_store = None
redis_deal = None


def setup_log(config_name):
    """配置日志"""

    # 设置日志的记录等级
    logging.basicConfig(level=config_map[config_name].LOG_LEVEL)  # 调试debug级
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = TimedRotatingFileHandler("logs/log", when='MIDNIGHT', interval=1, backupCount=10, encoding='utf-8')
    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(filename)s %(lineno)s %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter)
    # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


def create_app(config_name='production'):
    # 开启logging日志
    setup_log(config_name)

    # 创建项目app
    app = Flask(__name__)
    config_class = config_map.get(config_name)
    app.config.from_object(config_class)

    # redis配置
    global redis_store, redis_deal
    redis_store = redis.StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_POST, db=1, decode_responses=True)
    redis_deal = redis.StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_POST, db=2, decode_responses=True)

    # ws服务器开启
    if config_map[config_name].DEBUG:
        # debug模式下flask默认启动两个进程，以下可以保证只执行一次
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            start_thread()
    else:
        start_thread()

    # 注册扩展
    register_extensions(app)
    register_blueprints(app)
    register_commands(app)
    return app


def register_extensions(app):
    """注册扩展"""

    db.init_app(app)

    # 开启session会话保持
    Session(app)


def register_blueprints(app):
    """注册蓝图"""
    from qts.views.inspect import index_blue
    app.register_blueprint(index_blue)

    from qts.views.user import user_blue
    app.register_blueprint(user_blue)

    from qts.views.order import order_blue
    app.register_blueprint(order_blue)

    from qts.views.login import login_blue
    app.register_blueprint(login_blue)

    from qts.views.account import account_blue
    app.register_blueprint(account_blue)

    from qts.views.order_book import orderBook_blue
    app.register_blueprint(orderBook_blue)

    from qts.views.brush_order import brushOrder_blue
    app.register_blueprint(brushOrder_blue)

    from qts.views.damping_order import dampingOrder_blue
    app.register_blueprint(dampingOrder_blue)

    from qts.views.algorithmic import TWAP_blue
    app.register_blueprint(TWAP_blue)

    from qts.views.power import power_blue
    app.register_blueprint(power_blue)

    from qts.views.analyze import analyze_blue
    app.register_blueprint(analyze_blue)


def register_commands(app):
    """注册命令"""
    pass

import redis
import logging

from qts.constants import MYSQL_USER, MYSQL_PASSWORD, MYSQL_HOST, MYSQL_DB
from datetime import timedelta
from celery.schedules import crontab
import logging.config


class Config(object):
    DEBUG = True
    # 默认日志等级
    LOG_LEVEL = logging.WARNING
    SECRET_KEY = 'qtsIqkY0LFb8CbVdt8nha4eAduMvEq9upV0pSHLI7zM3fUQ/VK2t6cjtj5yJE3JzpJ8rROsHrrxeWel6VboCxQ=='
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://{USER}:{PASSWORD}@{HOST}:3306/{DB}'.format(USER=MYSQL_USER,PASSWORD=MYSQL_PASSWORD,HOST=MYSQL_HOST,DB=MYSQL_DB)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 试图函数执行完成后自动提交或回滚
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_ECHO = False

    # redis设置
    REDIS_HOST = '172.18.0.4'
    REDIS_POST = 6379

    # 设置session存储位置
    SESSION_TYPE = 'redis'
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_POST)
    SESS_USE_SIGNER = True
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24
    # SESSION_COOKIE_HTTPONLY = False #HttpOnly解决的是XSS后的Cookie劫持攻击

    # 是否开启Flask-APScheduler提供的api
    SCHEDULER_API_ENABLED = False

    # 初始化celery
    CELERY_BROKER_URL = 'redis://{}:6379/7'.format(REDIS_HOST)
    CELERY_RESULT_BACKEND = 'redis://{}:6379/8'.format(REDIS_HOST)
    # 配置时区
    CELERY_TIMEZONE = 'Asia/Shanghai'

    CELERYBEAT_SCHEDULE = {
        'each_1hours_task': {
            'task': 'celery_task.task.account_balance',
            'schedule': timedelta(hours=6),
            'args': (1, 1),
            'options': {'queue': 'fans_followers', 'routing_key': 'for_fans_follwers'},
        },
        'each_12hours_task': {
            'task': 'celery_task.task.deposit_withdraw_history',
            'schedule': timedelta(hours=12),
            'args': (12, 12),
            'options': {'queue': 'fans_followers', 'routing_key': 'for_fans_follwers'},
        },
        'each_24hours_task': {
            'task': 'celery_task.task.trading_record',
            'schedule': timedelta(hours=24),
            'args': (24, 24),
            'options': {'queue': 'fans_followers', 'routing_key': 'for_fans_follwers'},
        },
    }


class DevelopmentConfig(Config):
    DEBUG = True
    USE_RELOADER = False


class ProduactionConfig(Config):
    DEBUG = False
    # 默认日志等级
    LOG_LEVEL = logging.ERROR


config_map = {
    'development': DevelopmentConfig,
    'production': ProduactionConfig,
}
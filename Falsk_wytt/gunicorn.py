# encoding: utf-8
import multiprocessing
# from gevent import monkey
# monkey.patch_all()

# 监听端口
bind = '0.0.0.0:5000'
# 工作模式为gevent  eventlet
worker_class = 'gevent'  # 必须先安装gevent
# 并行工作进程数(我采用跟CPU核心数一致)
# 开启进程
# workers = multiprocessing.cpu_count() * 2 + 1
workers = 1
# 每个进程的开启线程
# threads = multiprocessing.cpu_count() * 2
# 设置最大并发量
# worker_connections = 2000
# 设置守护进程 True为后台运行
daemon = False
# 显示现在的配置，默认值为False，即显示。
check_config = False
# 设置进程文件目录
# pidfile = 'gunicorn.pid'
# 设置日志记录水平
loglevel = 'debug'
# 设置错误信息日志路径 ，设置里错误日志路径后将不再屏幕打印调试信息
errorlog = './logs/error.log'
# 设置访问日志路径
accesslog = './logs/access.log'
# 代码发生变化是否自动重启
reload = True

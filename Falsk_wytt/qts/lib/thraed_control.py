import threading
from qts.lib.accounts import get_user_info
from qts.lib.depth import depth_
from qts.lib.strategy_control import deal_strategy


def start_thread():
    # 深度获取线程
    threading.Thread(target=depth_,).start()

    # 用户资料获取线程
    threading.Thread(target=get_user_info,).start()

    # 重启所有策略
    # threading.Thread(target=deal_strategy,).start()

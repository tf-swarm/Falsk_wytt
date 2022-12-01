# -*- coding:utf-8 -*-
from threading import Thread
from qts.constants import Control
import inspect
import ctypes


def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)


# def thread_spread_out(strategy, params):
#     book = StrategyManager()
#     res_id = book.run(strategy, params)
#     # thr = Thread(target=book.run, args=(strategy, params))
#     # thr.start()
#
#
# def spread_out_terminate(plan_id):
#     print("-----plan_id", plan_id, Control)
#     if plan_id not in Control:
#         status = False
#     else:
#         status = True
#     return status
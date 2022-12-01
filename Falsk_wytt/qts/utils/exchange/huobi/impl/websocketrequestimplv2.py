import time

from qts.utils.exchange.huobi.constant.system import ApiVersion
from qts.utils.exchange.huobi.impl.websocketrequest import WebsocketRequest
from qts.utils.exchange.huobi.impl.utils.channels import *
from qts.utils.exchange.huobi.impl.utils.inputchecker import *
from qts.utils.exchange.huobi.model import *
from qts.utils.exchange.huobi.model.ordersupdateevent import OrdersUpdateEvent


class WebsocketRequestImplV2(object):

    def __init__(self, api_key):
        self.__api_key = api_key

    def subscribe_trade_clearing_event(self, symbols, callback, error_handler=None):
        if ("*" in symbols):
            symbols = ["*"]
        else:
            check_symbol_list(symbols)

        check_should_not_none(callback, "callback")

        def subscription_handler(connection):
            for val in symbols:
                connection.send(trade_clearing_channel(val))
                time.sleep(0.01)

        request = WebsocketRequest()
        request.subscription_handler = subscription_handler
        request.auto_close = False
        request.is_trading = True
        request.json_parser = TradeClearingEvent.json_parse
        request.update_callback = callback
        request.error_handler = error_handler
        request.api_version = ApiVersion.VERSION_V2
        return request

    def subscribe_accounts_update_event(self, mode, callback, error_handler=None):
        check_should_not_none(callback, "callback")
        if str(mode) == AccountBalanceMode.TOTAL:
            mode = AccountBalanceMode.TOTAL
        else:
            mode = AccountBalanceMode.BALANCE

        def subscription_handler(connection):
            connection.send(accounts_update_channel(mode))

        request = WebsocketRequest()
        request.subscription_handler = subscription_handler
        request.auto_close = False
        request.is_trading = True
        request.json_parser = AccountsUpdateEvent.json_parse
        request.update_callback = callback
        request.error_handler = error_handler
        request.api_version = ApiVersion.VERSION_V2
        return request

    def subscribe_orders_update_event(self, symbol, callback, error_handler=None):
        check_should_not_none(symbol, "symbol")
        check_should_not_none(callback, "callback")

        def subscription_handler(connection):
            connection.send(orders_update_channel(symbol))

        request = WebsocketRequest()
        request.subscription_handler = subscription_handler
        request.auto_close = False
        request.is_trading = True
        request.json_parser = OrdersUpdateEvent.json_parse
        request.update_callback = callback
        request.error_handler = error_handler
        request.api_version = ApiVersion.VERSION_V2
        return request
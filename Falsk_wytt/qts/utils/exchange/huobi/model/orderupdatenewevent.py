from qts.utils.exchange.huobi.model import *
from qts.utils.exchange.huobi.model.orderupdatenew import OrderUpdateNew


class OrderUpdateNewEvent:
    """
    The order update received by subscription of order update.

    :member
        symbol: The symbol you subscribed.
        timestamp: The UNIX formatted timestamp generated by server in UTC.
        data: The order detail.

    """

    def __init__(self):
        self.symbol = ""
        self.timestamp = 0
        self.data = OrderUpdateNew()

    def print_object(self, format_data=""):
        from huobi.base.printobject import PrintBasic
        PrintBasic.print_basic(self.symbol, "Symbol")
        PrintBasic.print_basic(self.timestamp, "Timestamp")

        orderupdatenew = self.data
        orderupdatenew.print_object()
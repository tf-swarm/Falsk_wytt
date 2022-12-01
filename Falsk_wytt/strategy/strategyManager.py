import uuid
from strategy.brushorder.brushorder import CBrushOrder
from strategy.orderbook.orderbook import COrderBook
from strategy.dampingorder.dampingOrder import CDampingOrder


class StrategyManager(object):

    def run(self, strategy_type, params):
        strategy = ""
        if strategy_type == "brushorder":
            strategy = CBrushOrder(params)
        elif strategy_type == "orderbook":
            strategy = COrderBook(params)
        elif strategy_type == "dampingorder":
            strategy = CDampingOrder(params)

        strategy.start()


strategyManager = StrategyManager()

if __name__ == '__main__':
    print(str(uuid.uuid1()))
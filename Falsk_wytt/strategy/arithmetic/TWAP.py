#coding:utf-8
import os
import yaml
import time
import random
from qts.utils.exchange.TAIBI.taibiApi import CTB
# from Exchange.binance.binanceApi import CBinance


class TWAP(object):
    def __init__(self, exchange, symbol):
        # threading.Thread.__init__(self)
        self.symbol = symbol
        self.exchange = exchange
        self.yml_path = os.path.join(os.getcwd(), 'T_wap.yml')
        with open(self.yml_path, 'r', encoding='UTF-8') as f:
            data = yaml.safe_load(f.read())
        # print(data)

        file_info = data[exchange][symbol]
        self.api_key = file_info['api_key']
        self.api_secret = file_info['api_secret']
        self.pricePrecision = file_info['pricePrecision']
        self.amountPrecision = file_info['amountPrecision']
        self.Amount = file_info['maxAmount']
        self.Time = file_info['order_time']
        self.delay = file_info['delay']

        if exchange == 'TAIBI':
            self.api = CTB(self.api_key, self.api_secret)
        # if exchange == 'BINANCE':
        #     self.api = CBinance(self.api_key, self.api_secret)
        #     self.symbol = symbol.replace('/', '')

    def get_buy_price(self):
        try:
            # {'buyprice': 0.02, 'sellprice': 0.04, 'lastprice': 0.020597}
            res_ticker = self.api.get_ticker(symbol=self.symbol)
            return res_ticker
        except Exception as e:
            print("ticker_return:{}".format(e))
            return -1

    def calc_Twap(self, side):
        try:
            price = self.get_buy_price()
            # print("----price", price)
            buy_price, sell_price = price["buyprice"], price["sellprice"]
            order_price = round((buy_price + sell_price) / 2, self.pricePrecision)
            print("----order_price", order_price)
            # last_price = price.get("lastprice", 0)
            number = int((int(self.Time) * 60) / self.delay)  # 15 秒
            for s in range(number):
                average = round(float(self.Amount / (number - s)), self.amountPrecision)
                print("剩下下单次数：{}, 下单数量：{}, 剩下下单数量：{}".format(number-s, average, self.Amount))
                if side == 1:
                    order_id = self.api.Buy(self.symbol, order_price, average)
                else:
                    randint_data = random.randint(1, 5)
                    print("---randint_data", randint_data)
                    buy_id = self.api.Buy(self.symbol, order_price, randint_data)
                    order_id = self.api.Sell(self.symbol, order_price, average)
                time.sleep(5)
                parse_number = self.get_trade_amount(order_id, average)
                # 取消订单
                cancel = self.api.cancel_order(order_id)
                if side == 2:
                    cancel_id = self.api.cancel_order(buy_id)
                    print("---cancel_id", cancel_id)
                # if self.exchange == 'TAIBI':
                #     cancel = self.api.cancel_order(order_id)
                # else:
                #     cancel = self.api.cancel_order(self.symbol, order_id)
                print("---cancel", cancel)
                self.Amount = self.Amount - float(parse_number)
                print("----amount", self.Amount)
                time.sleep(int(self.delay) - 5)
        except Exception as e:
            print(e)

    def get_trade_amount(self, order_id, average):
        parse, number = True, 0
        res = self.api.get_orders(self.symbol)
        # while parse:
        #     res = self.api.get_orders(self.symbol)
        #     if res != -1:
        #         break
        #     else:
        #         time.sleep(2)
        for order_info in res:
            if order_id == order_info["entrust_id"]:
                number = float(order_info["traded_num"])
            else:
                continue
        parse_number = (average if number == 0 else number)
        return parse_number

    def get_account(self):
        res = self.api.get_account()
        return res


if __name__ == '__main__':
    # api_key = 'FeY0y3dP5HKM4b7X95QBa3ysRDmrWj3Fn9jLJKmqqvgob8FTQHXzQtFBjM68h0pL'
    # api_secret = 'SO3AgukQpWfdRAyvFyvIg3cVSksDt4sMcNGP8B8S0AZUxd30i9YHucFpQs7vK2JY'
    twap = TWAP("TAIBI", "WTA/WTC")
    # [{'asset': 'WTA', 'free': 50.6886, 'locked': 0.0}, {'asset': 'WTC', 'free': 96.1018631637, 'locked': 0.0}]
    print(twap.get_account())

    # 1 buy  2 sell
    # start_time = time.time()
    # twap.calc_Twap(2)
    # print("--count_time", time.time() - start_time)

    # MarketMaker = TWAP('BINANCE', 'WTC/USDT')
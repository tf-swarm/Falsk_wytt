from qts.utils.exchange.BITHUMB.client import Bithumb
import time


class CBithumb:
    def __init__(self, akey, skey):
        self.bithumb = Bithumb(akey, skey)

    def get_account(self, symbol):
        try:
            accounts = {}
            resp = self.bithumb.get_balance(symbol)
            return resp
        except Exception as e:
            print(e)
            return -1

    def get_currency(self, coin):
        '''
        获取币资产余额 可用+冻结的
        return 余额
        '''
        try:
            acc = self.get_account(coin)
            return acc[0]
        except Exception as e:
            print(e)
            return None

    def get_ticker(self, symbol):
        """
        得到ticker数据
        param symbol
        return {买一价 卖一家 最后成交价}
        """
        ticker = {"buyprice":-1,"sellprice":-1,"lastprice":-1}
        try:
            depth = self.bithumb.get_orderbook(symbol)
            #print(depth,type(depth))
            ticker["buyprice"] = depth['bids'][0]['price']
            ticker["sellprice"] = depth['asks'][0]['price']
            ticker["lastprice"] = self.bithumb.get_current_price(symbol)

        except Exception as e:
            print(e)
        return ticker

    def Buy(self, symbol, price, amount):
        try:
            buyid = self.bithumb.buy_limit_order(symbol, price, amount)
            return buyid
        except Exception as e:
            print(e)
            return -1

    def Sell(self, symbol, price, amount):
        try:
            sellid = self.bithumb.sell_limit_order(symbol, price, amount)
            return sellid
        except Exception as e:
            print(e)

    def cancel_order(self, symbol, type, orderid):
        try:
            res = self.bithumb.cancel_order(symbol, type, orderid)
            return res
        except Exception as e:
            print(e)
            return -1

    def get_order(self, symbol, orderid):
        try:
            resp = self.bithumb.get_order_completed(symbol, orderid)
            return resp
        except Exception as e:
            print(e)
            return -1

    def get_orders(self, symbol):
        try:
            resp = self.bithumb.get_outstanding_order(symbol)
            return resp
        except Exception as e:
            print(e)
            return -1

    def cancel_all_orders(self, symbol):
        try:
            orders = self.get_orders(symbol)
            for o in orders:
                self.cancel_order(symbol, o['type'], o['order_id'])
                time.sleep(0.01)
        except Exception as e:
            print(e)

    def get_market_depth(self, symbol, limit=20):
        """
        深度数据
        """
        depth_info = {}
        try:
            result = self.bithumb.get_orderbook(order_currency=symbol, limit=limit)
            bids_list, asks_list = [], []
            for bid, ask in zip(result["bids"], result["asks"]):
                bids_list.append([bid["price"], bid["quantity"]])
                asks_list.append([ask["price"], ask["quantity"]])
            depth_info.update({"ts": result["timestamp"], "bids": bids_list, "asks": asks_list})
        except Exception as e:
            print(e)
        return depth_info


if __name__ == '__main__':
    # bithumb = CBithumb('b9bb112dd5b09467d54222503c48914c', 'b70de94faa1947a46b8ad3463a073187')
    # bithumb.get_ticker('ETH')

    bithumb = CBithumb('cb1add44620e762fe40f46009bc4ea70', '28578b0b758a9671f96cceee38bfa574')
    res = bithumb.get_market_depth('WTC')
    print(res)

    # acc = bithumb.get_account('WTC')
    # print(acc)
    # buyid = bithumb.Sell('WTC', 474, 1000)
    
    # print(buyid)

    # buyid2 = bithumb.Sell('WTC', 357.5, 6)
    
    # print(buyid2)

    # res = bithumb.get_order('WTC', buyid)
    # print(res)

    # res = bithumb.get_order('WTC', buyid)
    # print(res)

    # print(bithumb.cancel_order('WTC', 'ask', 'C0154000000034096164'))

    #bithumb.cancel_orders('WTC')

    # orders = bithumb.get_orders('WTC')
    # print(orders)



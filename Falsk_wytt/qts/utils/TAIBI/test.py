# from clientApi import TaBiApi
from qts.utils.TAIBI.clientApi import TaBiApi

if __name__ =='__main__':
    # api_key ='122bd3dda9b1700035a4d9f706a3c903'
    # api_secret ='e5381d1a0607d0f6e88968592825577d'

    api_key = 'bb2e2e9d2630dabedb0ea1e4366c9d67'
    api_secret = '6fe7bd45c68dad0f775b65b15c7b28ef'

    # api_key = '19e10848b1df9b4036e7e6519f2f9adb'
    # api_secret = 'd5abe2cab4d36d84d76b993b2f066370'

    # access_key = 'afdde84d6e4f0b0318f036b92fbb4fc2'
    # access_secret = '30514cbf721625094c4f1b74f24796e2'

    res = TaBiApi(key=api_key, secret=api_secret).get_balance()
    # print('res', res)
    # for bal in res['data']:
    #     if float(bal['qty']) >0 or float(bal['freeze_qty']) >0 or float( bal['otc_freeze_amount']) >0:
    #         print(bal)
    accs = res['data']
    accs = filter(lambda x: float(x['qty']) + float(x['freeze_qty']), accs)
    balances = []
    for acc in list(accs):
        balance = {}
        balance['asset'] = acc['symbol'].upper()
        balance['free'] = float(acc['qty'])
        balance['locked'] = float(acc['freeze_qty'])
        balances.append(balance)
    print("----balances-----", balances)

    # 批量下单
    # order_list = [
    #     {"price": 2.1, "qty": 52},
    #     {"price": 2.2,  "qty": 124},
    # ]
    #orders {'symbol': 'BTC/USDT', 'side': 1, 'ts': 1599807538075731200, 'orders': [{'qty': 0.001, 'price': 6000}]}
    #       {'symbol': 'TBI/USDT', 'side': 'BUY', 'ts': 1599807969393758976, 'orders': [{'price': 0.23, 'qty': 100.4}, {'price': 0.24, 'qty': 124}]}
    # res = TaBiApi(key=access_key, secret=access_secret).batch_order(symbol='TBI/USDT',side=2,order_list=order_list)
    # print('res', res)


    #批量撤单
    # id_list = [1304317777724579840]
    # res = TaBiApi(key=access_key, secret=access_secret).batch_cancel(order_id_list=id_list)
    # print('res', res)

    # res = TaBiApi(key=api_key, secret=api_secret).query_orderList(symbol='WTA/WTC', type=1)
    # print('res', res)
    # new_asks, new_bids = [], []
    # for order in res['data']:
    #     if order['opt'] == 1:
    #         new_bids.append(order)
    #     else:
    #         new_asks.append(order)
    # print("-----new_bids------", new_bids)


    # res = TaBiApi(key=access_key, secret=access_secret).deal_order_list(symbol='TBI/USDT',type=1,page=0,size=10)
    # print('res', res)

    # res = TaBiApi(key=api_key, secret=api_secret).get_kline(symbol='TBI/USDT',limit = 100,period='1min')
    # print('res', res)
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    # res = TaBiApi().get_depth(symbol='TBI/USDT',limit=100)
    # print('res',res)

    # res = TaBiApi(key=api_key, secret=api_secret).query_orderList_status(symbol='TBI/USDT', state='padding', page=1, size=10)
    # print('res', res)

    # res = TaBiApi(key=api_key, secret=api_secret).order_info(order_id=1304327323759157248)
    # print('res', res)

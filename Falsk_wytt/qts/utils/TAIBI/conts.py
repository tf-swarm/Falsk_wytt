
# BASEURL = 'https://app.taibi.io/open_api'
BASEURL = "https://openapi.taibi.io/open_api"
TESTURL = 'https://testapp.taibi.io/open_api'

HTTP_GET_BALANCE = '/api/v1/query/user/balance'  #获取余额
HTTP_BATCH_CREATE = '/api/v1/order/batch/create'  #批量下单
HTTP_QUERY_ORDER_LIST = '/api/v1/query/order/list' #查询订单
HTTP_QUERY_ORDER_LIST_STATUE = '/api/v1/query/order/list_by_state' #根据订单状态查询订单
HTTP_BATCH_CANCEL_ORDER = '/api/v1/order/batch/cancel' #批量撤单
HTTP_DEAL_RECORD =  '/api/v1/query/trade/records' #成交记录查询
HTTP_GET_ORDER_INFO = '/api/v1/query/order/info' #获取订单详情


HTTP_RECHARGE_RECORD = '/api/vin/list' #充值记录
HTTP_WITHDRAW_DEPOSIT_RECORD = '/api/out/list' #提币记录
HTTP_HOLD_CURRENCY = '/api/fin/list'  #所有用户持仓明细接口
HTTP_DEAL_RECORD_ALL = '/api/order/list'  #所以用户历史成交
HTTP_DEPTHDETAIL = '/api/handicap/list'  #订单详情

HTTP_TEST_DEPTH = 'http://ec2-18-140-57-24.ap-southeast-1.compute.amazonaws.com/depthWSURL/api/v1/query/market/depth'
HTTP_KLINE = '/api/v1/query/kline/period'

WS_DEPTH_TRADE = 'wss://app.taibi.io/depthWSURL/api/v1/ws/market'
WS_TEST_DEPTH_SOCKET = 'wss://testapp.taibi.io/depthWSURL/api/v1/ws/market'
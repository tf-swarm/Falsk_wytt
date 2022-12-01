import json
from qts.utils.exchange.huobi.impl.utils.jsonwrapper import JsonWrapper


def parse_json_from_string(value):
    return JsonWrapper(json.loads(value))

import os
import dotenv
import requests
import hashlib
import hmac
import json
import datetime
from urllib.parse import urlencode

dotenv.load_dotenv('.env')
api_key = os.environ.get("API_KEY")
secret_key = os.environ.get("SECRET_KEY")


def req(method, url, params={}):
    # signature
    servertime = requests.get(
        "https://api.binance.com/api/v3/time").json()['serverTime']
    params['timestamp'] = servertime
    _params = urlencode(params)
    # hmac
    hashedsig = hmac.new(secret_key.encode('utf-8'), _params.encode('utf-8'),
                         hashlib.sha256).hexdigest()
    params['signature'] = hashedsig

    # request
    match method:
        case "GET":
            res = requests.get(url, params=params, headers={
                               "X-MBX-APIKEY": api_key})
        case "POST":
            res = requests.post(url, params=params, headers={
                "X-MBX-APIKEY": api_key})
    return res.json()


balances = req("GET", "https://api.binance.com/api/v3/account")['balances']
for i in balances:
    if i['asset'] == "BUSD":
        print(i)

test_order = req(
    "POST", "https://api.binance.com/api/v3/order/test",
    {"symbol": "KDABUSD", "side": "BUY", "type": "MARKET", "quoteOrderQty": 100})
print(test_order)

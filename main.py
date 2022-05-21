import os
import dotenv
import requests
import hashlib
import hmac
import time
from urllib.parse import urlencode
from configparser import ConfigParser

# load config.ini
config = ConfigParser().read('./config.ini')

# settings
if bool(config['binance']['testnet']) == True:
    base_url = config['binance']['testnet_url']
    api_key = config['binance']['api_key_testnet']
    secret_key = config['binance']['secret_key_testnet']
else:
    # load .env
    dotenv.load_dotenv('.env')
    base_url = config['binance']['url']
    api_key = os.environ.get("API_KEY")
    secret_key = os.environ.get("SECRET_KEY")
# duo mode setup
asset_symbol = config['duo']['asset_symbol']
asset_balance = float(config['duo']['asset_balance'])
asset_percentage = float(config['duo']['asset_percentage'])
stable_asset_symbol = config['duo']['stable_asset_symbol']
stable_asset_balance = float(config['duo']['stable_asset_balance'])
symbol = asset_symbol+stable_asset_symbol


def req(method: str, url: str, params: dict[object, object] = {}, **kwargs):
    if 'auth' not in kwargs:
        kwargs['auth'] = False

    if kwargs['auth'] == True:
        # signature
        servertime = requests.get(
            base_url+"/api/v3/time").json()['serverTime']
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
    res = res.json()
    if "code" in res and res['code'] != 200:
        print(res, end="\n\n")
    return res


def get_balances(symbols: str):
    res = req("GET", base_url + "/api/v3/account", {}, auth=True)
    balances = res['balances']
    balances_dict = {}
    for s in symbols:
        for a in balances:
            if a['asset'] == s:
                balances_dict[s] = a
    return balances_dict


def new_order(symbol: str, side: str, type: str, **kwargs):
    if type == "MARKET":
        if 'quantity' not in kwargs and 'quoteOrderQty' not in kwargs:
            raise Exception("require quantity || quoteOrderQty")
        res = req(
            "POST", base_url+"/api/v3/order",
            {"symbol": symbol, "side": side, "type": type, "quoteOrderQty": kwargs['quoteOrderQty']}, auth=True)
        return res

    if type == "LIMIT":
        if 'timeInForce' not in kwargs or 'quantity' not in kwargs or 'price' not in kwargs:
            raise Exception("require timeInForce & quantity & price")
        res = req(
            "POST", base_url+"/api/v3/order",
            {"symbol": symbol, "side": side, "type": type, "timeInForce": kwargs['timeInForce'], "quantity": kwargs['quantity'], "price": kwargs['price']}, auth=True)
        return res


# real account balance check
binance_balances = get_balances([stable_asset_symbol, asset_symbol])
binance_asset_balance = float(binance_balances[asset_symbol]['free'])
binance_stable_asset_balance = float(binance_balances[stable_asset_symbol]['free'])
if binance_asset_balance < asset_balance or binance_stable_asset_balance < stable_asset_balance:
    raise Exception("account balance not enough")

print("Binance Spot Account Balance\n{}: {}\n{}: {}\n".format(asset_symbol,
                                                              binance_asset_balance, stable_asset_symbol, binance_stable_asset_balance))
print("Configured Balance\n{}: {}\n{}: {}\n".format(asset_symbol,
                                               asset_balance, stable_asset_symbol, stable_asset_balance))

while(1):
    # check exhange pair
    exchange_info = req("GET", base_url+"/api/v3/exchangeInfo",
                        {"symbol": symbol})['symbols'][0]
    symbol_status = exchange_info['status']

    if symbol_status != "TRADING":
        raise Exception("binance suspended trading!")

    print("{}: {}\n{}: {}".format(asset_symbol,
          round(asset_balance, 8), stable_asset_symbol, stable_asset_balance))

    # calculate rebalance value
    asset_price = float(req("GET", base_url+"/api/v3/ticker/price",
                             {"symbol": symbol})['price'])
    asset_current_value = asset_balance*asset_price

    rebalanced_value = int((asset_current_value+stable_asset_balance)*(asset_percentage/100))

    print("position_value: {}\nrebalanced_value: {}".format(
        rebalanced_value*2, rebalanced_value))

    # rebalance trade conditions
    value_delta = int(asset_current_value-rebalanced_value)
    print("value_delta: {}".format(value_delta))
    if abs(value_delta) > 30:
        if value_delta < 0:
            order = new_order(symbol, "BUY", "MARKET",
                              quoteOrderQty=abs(value_delta))
            asset_balance = rebalanced_value/asset_price
            stable_asset_balance = rebalanced_value
        elif value_delta > 0:
            order = new_order(symbol, "SELL", "MARKET",
                              quoteOrderQty=abs(value_delta))
            asset_balance = rebalanced_value/asset_price
            stable_asset_balance = rebalanced_value

    print()
    time.sleep(60)

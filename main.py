import os
from tkinter.messagebox import NO
import dotenv
import requests
import hashlib
import hmac
import time
from urllib.parse import urlencode
from configparser import ConfigParser
import json
from tech_ana import check_ta
from history_log import add_row, write_csv
from datetime import datetime

# load config.ini
config = ConfigParser()
config.read('config.ini')
# settings
if int(config['binance']['testnet']) == 1:
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
asset_symbol = config['duo_mode']['asset_symbol']
asset_balance = float(config['duo_mode']['asset_balance'])
stable_asset_symbol = config['duo_mode']['stable_asset_symbol']
stable_asset_balance = float(config['duo_mode']['stable_asset_balance'])
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


# real account balance check
binance_balances = get_balances([stable_asset_symbol, asset_symbol])
binance_asset_balance = float(binance_balances[asset_symbol]['free'])
binance_stable_asset_balance = float(
    binance_balances[stable_asset_symbol]['free'])
if binance_asset_balance < asset_balance or binance_stable_asset_balance < stable_asset_balance:
    raise Exception("account balance not enough")

print("Binance Spot Account Balance\n{}: {}\n{}: {}\n".format(asset_symbol,
                                                              binance_asset_balance, stable_asset_symbol, binance_stable_asset_balance))
print("Configured Balance\n{}: {}\n{}: {}\n".format(asset_symbol,
                                                    asset_balance, stable_asset_symbol, stable_asset_balance))

# auto_asset_start_price setup
asset_start_price = None
if int(config['duo_mode']['auto_asset_start_price']) == 1:
    asset_start_price = float(req("GET", base_url+"/api/v3/ticker/price",
                                  {"symbol": symbol})['price'])
else:
    asset_start_price = float(config['duo_mode']['asset_start_price'])

rebalance_trig_pct = int(config['duo_mode']['rebalance_trig_pct'])
rebalance_trig_pct_price_range = round(
    rebalance_trig_pct/100*asset_start_price, 2)

last_re_price = asset_start_price

first_re = int(config['duo_mode']['first_re'])

print("asset_start_price:", asset_start_price)
print("rebalance_trig_pct:", rebalance_trig_pct)
print("rebalance_trig_pct_price_range:", rebalance_trig_pct_price_range)

while(1):
    try:
        # re config
        config.read('config.ini')
        dynamic_asset_ratio_upside = json.loads(
            config['duo_mode']['dynamic_asset_ratio_upside'])
        dynamic_asset_ratio_downside = json.loads(
            config['duo_mode']['dynamic_asset_ratio_downside'])
        asset_ratio_stable = float(config['duo_mode']['asset_ratio_stable'])

        # check exhange pair
        exchange_info = req("GET", base_url+"/api/v3/exchangeInfo",
                            {"symbol": symbol})['symbols'][0]
        symbol_status = exchange_info['status']

        if symbol_status != "TRADING":
            raise Exception("binance suspended trading!")

        print("{}: {}\n{}: {}".format(asset_symbol,
                                      round(asset_balance, 8), stable_asset_symbol, stable_asset_balance))

        # check price change
        asset_price = float(req("GET", base_url+"/api/v3/ticker/price",
                                {"symbol": symbol})['price'])
        asset_price_pct_change = round((
            (asset_price - asset_start_price) / asset_start_price)*100, 2)

        print("{}: {}\nasset_price_pct_change: {}".format(
            symbol, asset_price, asset_price_pct_change))

        # check asset ratio change
        asset_ratio = None
        if int(config['duo_mode']['enable_dynamic_asset_ratio']) == 1:
            if asset_price_pct_change >= 0:
                for k in dynamic_asset_ratio_upside.keys():
                    if asset_price_pct_change >= float(k):
                        asset_ratio = dynamic_asset_ratio_upside[k]
                        break
                    else:
                        asset_ratio = asset_ratio_stable
            elif asset_price_pct_change < 0:
                for k in dynamic_asset_ratio_downside.keys():
                    if asset_price_pct_change <= float(k):
                        asset_ratio = dynamic_asset_ratio_downside[k]
                        break
                    else:
                        asset_ratio = asset_ratio_stable
        else:
            asset_ratio = asset_ratio_stable

        print("asset_ratio(allocation): {}".format(asset_ratio))

        # calculate rebalance value
        asset_current_value = round(asset_balance*asset_price, 2)
        position_value = asset_current_value+stable_asset_balance
        asset_rebalanced_value = round(position_value*asset_ratio, 2)

        print("position_value: {}\nasset_current_value: {}\nasset_rebalanced_value: {}".format(
            round(position_value, 2), asset_current_value, asset_rebalanced_value))

        # rebalance trade conditions
        value_delta = round(asset_current_value-asset_rebalanced_value, 2)

        print("value_delta: {}".format(value_delta))
        print("last_re_price: {}\nprice change from last_re_price: {}".format(
            last_re_price, round(last_re_price-asset_price), 2))
        print("rebalance_trig_pct: {}\nrebalance_trig_pct_price_range: {}".format(
            rebalance_trig_pct, rebalance_trig_pct_price_range))

        if (abs(value_delta) > 30 and abs(last_re_price-asset_price) > rebalance_trig_pct_price_range) or first_re == 1:
            print('EXCUTE REBALANCE')
            ta = check_ta(symbol, '1h')
            print("check_ta:", ta)
            if (value_delta < 0 and ta) or (value_delta < 0 and first_re == 1):
                order = req("POST", base_url+"/api/v3/order", {"symbol": symbol, "side": "BUY",
                                                               "type": "MARKET", "quoteOrderQty": abs(value_delta)}, auth=True)
                asset_balance = asset_rebalanced_value/asset_price
                stable_asset_balance = position_value-asset_rebalanced_value
                last_re_price = asset_price
                # save history log
                add_row(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), symbol, "BUY", asset_price, asset_price_pct_change,
                        value_delta, asset_ratio, asset_balance, stable_asset_balance, position_value)
                write_csv()
            elif (value_delta > 0 and ta) or (value_delta > 0 and first_re == 1):
                order = req("POST", base_url+"/api/v3/order", {"symbol": symbol, "side": "SELL",
                                                               "type": "MARKET", "quoteOrderQty": abs(value_delta)}, auth=True)
                asset_balance = asset_rebalanced_value/asset_price
                stable_asset_balance = position_value-asset_rebalanced_value
                last_re_price = asset_price
                # save history log
                add_row(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), symbol, "SELL", asset_price, asset_price_pct_change,
                        value_delta, asset_ratio, asset_balance, stable_asset_balance, position_value)
                write_csv()
            first_re = 0
    except Exception as err:
        print(err)
    print("-------------------------------------------")
    time.sleep(60)

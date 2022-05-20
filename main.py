import os
import dotenv
import requests
import hashlib
import hmac
import time
from urllib.parse import urlencode
import typer

dotenv.load_dotenv('.env')
api_key = os.environ.get("API_KEY")
secret_key = os.environ.get("SECRET_KEY")
api_key_testnet = "32GVaaDL8rmcsOgtaoDf4WYHR5r3CB2FItkZctSgdrjEvTABTb7K3IaKaouT423K"
secret_key_testnet = "etctgwTsXj3XgYZ51hsvU2aensT17OR0eGO1tVVD4v1gsrC68LM3ZSPbHr3OAOBi"

base_url = "https://api.binance.com"
base_url_testnet = "https://testnet.binance.vision"
base_url = base_url_testnet
api_key = api_key_testnet
secret_key = secret_key_testnet


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


def get_candles(symbol: str, timeframe: str = '1h', limit: int = 500):  # 1h 4h 1d
    candles = req("GET", base_url+"/api/v3/klines",
                  {"symbol": symbol, "limit": limit, "interval": timeframe})
    return candles  # candles[-1] is newest


def rebalance_stable_5050(symbol_asset: str, asset_balance: float, symbol_stable: str, stable_balance: float):
    # account balance setup
    binance_balances = get_balances([symbol_stable, symbol_asset])
    binance_asset_balance = float(binance_balances[symbol_asset]['free'])
    binance_stable_balance = float(binance_balances[symbol_stable]['free'])
    if binance_asset_balance < asset_balance or binance_stable_balance < stable_balance:
        raise Exception("account balance not enough")

    print("Binance Spot Account Balance\n{}: {}\n{}: {}\n".format(symbol_asset,
                                                                  binance_asset_balance, symbol_stable, binance_stable_balance))
    print("Setup Balance\n{}: {}\n{}: {}\n".format(symbol_asset,
                                                   asset_balance, symbol_stable, stable_balance))

    while(1):
        # check exhange pair
        symbol = symbol_asset+symbol_stable
        exchange_info = req("GET", base_url+"/api/v3/exchangeInfo",
                            {"symbol": symbol})['symbols'][0]
        symbol_status = exchange_info['status']

        if symbol_status != "TRADING":
            raise Exception("binance suspended trading!")

        print("{}: {}\n{}: {}".format(symbol_asset,
              round(asset_balance, 8), symbol_stable, stable_balance))

        # calculate rebalance value
        asset_price = float(req("GET", base_url+"/api/v3/ticker/price",
                                {"symbol": symbol})['price'])
        asset_current_value = asset_balance*asset_price
        rebalanced_value = int((asset_current_value+stable_balance)/2)

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
                stable_balance = rebalanced_value
            elif value_delta > 0:
                order = new_order(symbol, "SELL", "MARKET",
                                  quoteOrderQty=abs(value_delta))
                asset_balance = rebalanced_value/asset_price
                stable_balance = rebalanced_value

        print()
        time.sleep(60)


app = typer.Typer()


@app.command()
def stable5050(symbol_asset: str, asset_balance: float, symbol_stable: str, stable_balance: float):
    rebalance_stable_5050(symbol_asset, asset_balance, symbol_stable, stable_balance)

if __name__ == "__main__":
    app()

#tenical analysis + percentage rebalance(>10%, 5%)
#ema 30 50 (trading ciew) stoch rsi(<>70 && cross) + rsi(<>50)
#EMA 10 ตัดกับ EMA 21  หากเส้น EMA 10 ตัดขึ้นซื้อเพิ่มเพราะมันลงมาสุดแล้ว ส่วน EMA 10 ตัดลงเราก็ขาย เพราะมันขึ้นมาสุดแล้ว โดยใช้ TIME FRAME DAY

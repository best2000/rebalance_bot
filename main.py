import os
import dotenv
import requests
import hashlib
import hmac
from urllib.parse import urlencode
from configparser import ConfigParser
import json
from tech_ana import check_ta
from history_log import add_row, write_csv
from datetime import datetime
import asyncio
from ftx_client import FtxClient


# load config.ini
config = ConfigParser()
config.read('./public/config.ini')
# load .env
dotenv.load_dotenv('.env')
api_key = os.environ.get("API_KEY")
secret_key = os.environ.get("SECRET_KEY")

client = FtxClient(api_key,
                   secret_key, config["config"]['sub_account'])

market_symbol = config["config"]["market_symbol"]
asset_symbol = market_symbol.split("/")[0]
stable_asset_symbol = market_symbol.split("/")[1]

# auto_asset_start_price setup
asset_start_price = None
if int(config["config"]['auto_asset_start_price']) == 1:
    asset_start_price = client.get_single_market(market_symbol)['bid']
else:
    asset_start_price = float(config["config"]['asset_start_price'])

last_re_price = asset_start_price

first_re = int(config["config"]['first_re'])

print('first_re:', first_re)
print("asset_start_price:", str(asset_start_price))


def get_balance(symbol):
    for a in client.get_balances():
        if a['coin'] == symbol:
            return a


async def wait():
    bar = [
        " | sleeping   ",
        " / sleeping.  ",
        " ─ sleeping.. ",
        " \ sleeping...",
    ]
    i = 0

    while True:
        print(bar[i % len(bar)], end="\r")
        await asyncio.sleep(0.1)
        i += 1


async def loop():
    asyncio.create_task(wait())
    while(1):
        global asset_start_price
        global first_re
        global last_re_price
        global asset_start_price
        global market_symbol
        global asset_symbol
        global stable_asset_symbol

        try:
            # re config
            config.read('./public/config.ini')
            dynamic_asset_ratio_upside = json.loads(
                config["config"]['dynamic_asset_ratio_upside'])
            dynamic_asset_ratio_downside = json.loads(
                config["config"]['dynamic_asset_ratio_downside'])
            asset_ratio_stable = float(
                config["config"]['asset_ratio_stable'])
            rebalance_trig_pct = int(config["config"]['rebalance_trig_pct'])

            # check balance
            asset_balance = get_balance(asset_symbol)['free']
            stable_asset_balance = get_balance(stable_asset_symbol)['free']

            market_info = client.get_single_market(market_symbol)
            # check exhange pair
            if market_info['enabled'] == False:
                raise Exception("FTX suspended trading!")

            # check price change (from start)
            asset_price = market_info['bid']
            asset_price_pct_change_start = (
                (asset_price - asset_start_price) / asset_start_price)*100

            # check asset ratio change
            asset_ratio = asset_ratio_stable
            if int(config["config"]['enable_dynamic_asset_ratio']) == 1:
                if asset_price_pct_change_start >= 0:
                    for k in dynamic_asset_ratio_upside.keys():
                        if asset_price_pct_change_start >= float(k):
                            asset_ratio = dynamic_asset_ratio_upside[k]
                            break
                        else:
                            asset_ratio = asset_ratio_stable
                elif asset_price_pct_change_start < 0:
                    for k in dynamic_asset_ratio_downside.keys():
                        if asset_price_pct_change_start <= float(k):
                            asset_ratio = dynamic_asset_ratio_downside[k]
                            break
                        else:
                            asset_ratio = asset_ratio_stable

            # calculate rebalance value
            asset_current_value = asset_balance*asset_price
            position_value = asset_current_value+stable_asset_balance
            asset_rebalanced_value = position_value*asset_ratio

            # rebalance trade conditions
            value_delta = asset_current_value-asset_rebalanced_value
            price_pct_change_last_re = abs(
                (last_re_price-asset_price/last_re_price)*100)

            # PRINT---
            os.system('cls' if os.name == 'nt' else 'clear')
            print("--------------------")
            print("\r[CONFIG]")
            print("symbol:", market_symbol)
            print("start_price:", asset_start_price)
            print("dynamic_asset_ratio_upside:", dynamic_asset_ratio_upside)
            print("dynamic_asset_ratio_downside:",
                  dynamic_asset_ratio_downside)
            print("asset_ratio_stable:", asset_ratio_stable)
            print("rebalance_trig_pct:", rebalance_trig_pct)
            print("-------------------")
            print("[STATUS]")
            print(asset_symbol+"_balance: "+str(asset_balance))
            print(stable_asset_symbol+"_balance: "+str(stable_asset_balance))
            print()
            print(asset_symbol+"_price: "+str(asset_price))
            print(asset_symbol+"_price_pct_change_start: " +
                  str(asset_price_pct_change_start))
            print("last_re_price:", str(last_re_price))
            print("price_change_from_last_re_price:",
                  str(asset_price-last_re_price))
            print("price_pct_change_last_re:",
                  str((asset_price-last_re_price)/last_re_price*100))
            print()
            print("rebalance_trig_pct:", str(rebalance_trig_pct))
            print(asset_symbol+"_ratio(allocation): "+str(asset_ratio))
            print()
            print("position_value:", str(position_value))
            print(asset_symbol+"_current_value(position): " +
                  str(asset_current_value))
            print(asset_symbol+"_rebalanced_value(position): " +
                  str(asset_rebalanced_value))
            print("value_delta:", str(value_delta))
            # --------

            if (abs(value_delta) > 10 and price_pct_change_last_re > rebalance_trig_pct) or first_re == 1:
                print("--------------------")
                print('[EXCUTE_REBALANCE]')
                ta = check_ta(market_symbol.replace('/', ''), '4h')
                print("check_ta:", ta)
                if (value_delta < 0 and ta) or (value_delta < 0 and first_re == 1):
                    client.place_order(market_symbol, 'buy', None, abs(
                        value_delta)/asset_price, "market")
                    last_re_price = asset_price
                    # save history log
                    add_row(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), market_symbol, "buy", asset_price, asset_price_pct_change_start,
                            value_delta, asset_ratio, asset_balance, stable_asset_balance, position_value)
                    write_csv()
                elif (value_delta > 0 and ta) or (value_delta > 0 and first_re == 1):
                    client.place_order(market_symbol, 'sell', None, abs(
                        value_delta)/asset_price, "market")
                    last_re_price = asset_price
                    # save history log
                    add_row(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), market_symbol, "sell", asset_price, asset_price_pct_change_start,
                            value_delta, asset_ratio, asset_balance, stable_asset_balance, position_value)
                    write_csv()
                first_re = 0
        except Exception as err:
            print(err)
        print("--------------------")
        await asyncio.sleep(300)
asyncio.run(loop())

import os
import dotenv
from configparser import ConfigParser
from ftx_client import FtxClient
import time


# load config.ini
config = ConfigParser()
config.read('./config.ini')
# load .env
dotenv.load_dotenv('.env')
api_key = os.environ.get("API_KEY")
secret_key = os.environ.get("SECRET_KEY")

sub_account = config["config"]["sub_account"]
bull_symbol = config["config"]["bull_symbol"]
bear_symbol = config["config"]["bear_symbol"]

client = FtxClient(api_key,
                   secret_key, config["config"]['sub_account'])      


bull_start_price = client.get_single_market(bull_symbol)['bid']
bear_start_price = client.get_single_market(bear_symbol)['bid']

while(1):
    try:
        market_info_bull = client.get_single_market(bull_symbol)
        market_info_bear = client.get_single_market(bear_symbol)

        # check price change (from start)
        bull_price = market_info_bull['bid']
        bear_price = market_info_bear['bid']
        bull_price_pct_change_start = round((
            (bull_price-bull_start_price) / bull_start_price)*100, 2)
        bear_price_pct_change_start = round((
            (bear_price-bear_start_price) / bear_start_price)*100, 2)

        # PRINT---
        os.system('cls' if os.name == 'nt' else 'clear')
        print("--------------------")
        print("\r[CONFIG]")
        print("sub_account:", sub_account)
        print("bull_symbol:", bull_symbol)
        print("bear_symbol:", bear_symbol)
        print("-------------------")
        print("[STATUS]")
        print("NAV_change%:", bull_price_pct_change_start +
              bear_price_pct_change_start)
        print(bull_symbol+"_price_change%: "+str(bull_price_pct_change_start))
        print(bear_symbol+"_price_change%: "+str(bear_price_pct_change_start))
        # --------
    except Exception as err:
        print(err)
    time.sleep(60)
    print("--------------------")

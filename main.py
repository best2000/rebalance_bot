from modules.ftx_client import FtxClient, instant_limit_order
from modules.trade_log import add_row
from modules.tech import check_ta
from configparser import ConfigParser
import pandas as pd
import dotenv
import os
import time
import math
import datetime
import sys
import logging
from logging.handlers import TimedRotatingFileHandler
from logging import Formatter


# logger setup
logger = logging.getLogger("main")

# create handler
handler = TimedRotatingFileHandler(
    filename='./logs/main.log', when='D', interval=1, backupCount=7, encoding='utf-8', delay=False)

formatter = Formatter(fmt='%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


class Bot:
    def __init__(self, conf_path: str = "./config.ini", env_path: str = "./.env"):
        # config
        self.conf_path = conf_path
        self.env_path = env_path
        self.read_config()
        # ftx client setup
        dotenv.load_dotenv(self.env_path)
        api_key = os.environ.get("API_FTX")
        secret_key = os.environ.get("SECRET_FTX")
        self.ftx_client = FtxClient(api_key,
                                    secret_key, self.sub_account)

        # symbol variables
        self.base_symbol = self.market_symbol.split('/')[0]
        self.quote_symbol = self.market_symbol.split('/')[1]

        # init price
        # check exhange pair and price
        self.market_info = self.ftx_client.get_single_market(
            self.market_symbol)
        if self.market_info['enabled'] == False:
            raise Exception("FTX suspended trading!")
        self.init_price = self.market_info['price']

        # calculate init nav
        self.base_symbol_balance = self.ftx_client.get_balance_specific(
            self.base_symbol)
        self.quote_symbol_balance = self.ftx_client.get_balance_specific(
            self.quote_symbol)
        self.init_nav = float(0 if not self.base_symbol_balance else self.base_symbol_balance['usdValue']) + float(
            0 if not self.quote_symbol_balance else self.quote_symbol_balance['usdValue'])
        
        # first update stats
        self.update_stats()

    def read_config(self):
        config = ConfigParser()
        config.read(self.conf_path)
        # main
        self.market_symbol = config['main']['market_symbol']
        self.sub_account = config["main"]['sub_account']
        # technical analysis
        #self.timeframe_buy = config["ta"]['timeframe_buy']

    def update_stats(self):
        # check exhange pair and price
        self.market_info = self.ftx_client.get_single_market(
            self.market_symbol)
        if self.market_info['enabled'] == False:
            raise Exception("FTX suspended trading!")
        # check price
        self.price = self.market_info['price']
        self.price_chg_pct = round(
            ((self.price-self.init_price)/self.init_price)*100, 2)
        # calculate nav
        self.base_symbol_balance = self.ftx_client.get_balance_specific(
            self.base_symbol)
        self.quote_symbol_balance = self.ftx_client.get_balance_specific(
            self.quote_symbol)
        self.nav = float(0 if not self.base_symbol_balance else self.base_symbol_balance['usdValue']) + float(
            0 if not self.quote_symbol_balance else self.quote_symbol_balance['usdValue'])
        self.nav_pct = self.nav/self.init_nav*100

    def display_stats(self):
        # os.system('cls' if os.name == 'nt' else 'clear')
        print("--------------------")
        print("[CONFIG]")
        print("market_symbol:", self.market_symbol)
        print("sub_account:", self.sub_account)
        print("-------------------")
        print("[STATUS]")
        print("{}: {}".format(self.market_symbol, self.price))
        print(self.base_symbol+" balance: " +
              str(round(float(0 if not self.base_symbol_balance else self.base_symbol_balance['free']), 4)))
        print(self.quote_symbol+" balance: " +
              str(round(float(0 if not self.quote_symbol_balance else self.quote_symbol_balance['free']), 2)))
        print("price_chg: "+str(self.price_chg_pct)+"%")
        print("NAV: "+str(round(self.nav, 2))+"/" +
              str(round(self.init_nav, 2))+" ["+str(int(self.nav_pct))+"%]")
        print("--------------------")
        print("timestamp:", datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        print("--------------------")

    def run(self):
        while True:
            try:
                # price tick
                self.update_stats()
                # update config
                self.read_config()

                traded = 0
                """
                # check ta signal
                ta_buy_df = check_ta(self.market_symbol, self.timeframe_buy,
                                     self.ema1_len_buy, self.ema2_len_buy, 100, name="buy")
                buy_sig = ta_buy_df.iloc[-2, -1]

                logger.debug(
                    "buy_sig={} | sell_sig={}".format(buy_sig, sell_sig))
                
                    # buy
                    if pos_val > 0:
                        pos_unit = pos_val/self.market_info['ask']
                        instant_limit_order(
                            self.ftx_client, self.market_symbol, "buy", pos_unit)
                        traded = 1

                        logger.debug("brought!")

                    # sell
                    if pos_hold > 0:
                        instant_limit_order(
                            self.ftx_client, self.market_symbol, "sell", pos_hold)
                        traded = 1

                        logger.debug("sold!")
                """

                # LOG
                if traded:
                    #logger.info("traded")
                    # re tick
                    self.update_stats()
                    # update log
                    add_row(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                            self.price, self.price_chg_pct, self.nav, self.nav_pct)

                # print stats
                self.display_stats()
            except Exception as err:
                print(err)
                logger.error(err)
            time.sleep(62)


bot = Bot()
# print(bot.grid)
# print(bot.grid_trading)
for k in bot.__dict__:
    print(k, ':', bot.__dict__[k])
bot.run()

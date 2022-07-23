from numpy import dstack
from modules.ftx_client import FtxClient, instant_limit_order
from modules.trade_log import add_row
from modules.tech import check_ta
from configparser import ConfigParser
import pandas as pd
import dotenv
import os
import time
import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
from logging import Formatter
import json
import pickle


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

        # last rb vars
        self.last_rb_price = -1

        # first update stats
        self.update_stats()

    def read_config(self):
        config = ConfigParser()
        config.read(self.conf_path)
        # main
        self.market_symbol = config['main']['market_symbol']
        self.sub_account = config["main"]['sub_account']
        # rb conditions
        self.trig_price_chg_thresh = float(config["rb"]['trig_price_chg_thresh'])
        self.base_ratio = float(config["rb"]['base_ratio'])
        # technical analysis
        self.timeframe = config["ta"]['timeframe']
        self.ema1_len = int(config["ta"]['ema1_len'])
        self.ema2_len = int(config["ta"]['ema2_len'])
        #self.ema3_len = int(config["ta"]['ema3_len'])
        self.rsi_len = int(config["ta"]['rsi_len'])

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
        # calculate stats
        self.base_symbol_balance = self.ftx_client.get_balance_specific(
            self.base_symbol)
        self.quote_symbol_balance = self.ftx_client.get_balance_specific(
            self.quote_symbol)
        self.base_symbol_balance_value = float(
            0 if not self.base_symbol_balance else self.base_symbol_balance['usdValue'])
        self.quote_symbol_balance_value = float(
            0 if not self.quote_symbol_balance else self.quote_symbol_balance['usdValue'])
        self.nav = self.base_symbol_balance_value + self.quote_symbol_balance_value
        self.base_symbol_balance_value_ratio_pct = round((
            self.base_symbol_balance_value/self.nav)*100, 2)
        self.nav_pct = self.nav/self.init_nav*100

        # last rb stats
        self.last_rb_price_chg_pct = round(((
            self.price - self.last_rb_price)/self.last_rb_price)*100, 2)

    def display_stats(self):
        # os.system('cls' if os.name == 'nt' else 'clear')
        print("--------------------")
        print("[CONFIG]")
        print("market_symbol:", self.market_symbol)
        print("sub_account:", self.sub_account)
        print("-------------------")
        print("[STATUS]")
        print("{}: {}".format(self.market_symbol, self.price))
        print(self.base_symbol+"_balance: " +
              str(round(float(0 if not self.base_symbol_balance else self.base_symbol_balance['free']), 4)))
        print(self.quote_symbol+"_balance: " +
              str(round(float(0 if not self.quote_symbol_balance else self.quote_symbol_balance['free']), 2)))
        print("{}_ratio: {}%".format(self.base_symbol,
              self.base_symbol_balance_value_ratio_pct))
        print("price_chg: "+str(self.price_chg_pct)+"%")
        print("last_rb_price: {}".format(self.last_rb_price))
        print("last_rb_price_chg: {}%".format(self.last_rb_price_chg_pct))
        print("NAV: {}/{} [{}%]".format(round(self.nav, 2),
              round(self.init_nav, 2), round(self.nav_pct, 2)))
        print("--------------------")
        print("timestamp:", datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
        print("--------------------")

    def save_instance(self):
        # json
        instance = dict(self.__dict__)  # make copy of dict
        instance['ftx_client'] = str(instance['ftx_client'])
        with open("./logs/instance.json", "w") as file_json:
            json.dump(instance, file_json, indent=4)
        # pickle
        with open('./instance.pkl', 'wb') as file_pkl:
            pickle.dump(self, file_pkl, pickle.HIGHEST_PROTOCOL)

    def run(self):
        while True:
            try:
                # price tick
                self.update_stats()
                self.save_instance()
                # update config
                self.read_config()

                """
                traded = 0
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


                # LOG
                if traded:
                    # logger.info("traded")
                    # re tick
                    self.update_stats()
                    self.save_instance_to_json()
                    # update log
                    add_row(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                            self.price, self.price_chg_pct, self.nav, self.nav_pct, self.base_symbol_balance_value_ratio_pct)
                """

                # print stats
                self.display_stats()
            except Exception as err:
                print(err)
                logger.error(err)
            time.sleep(65)


try:
    with open('./instance.pkl', 'rb') as file_pkl:
        read_instance = input("Use exist instance [y/n]?: ")
        if read_instance == "y":
            bot = pickle.load(file_pkl)
        elif read_instance == "n":
            raise Exception()
except Exception as err:
    bot = Bot()
finally:
    bot.run()

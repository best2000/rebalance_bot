from csv import reader
from modules.ftx_client import FtxClient, instant_limit_order
from modules.csv import add_row
from modules.tech import check_ta_ema, check_ta_rsi
from configparser import ConfigParser
import dotenv
import os
import time
import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
from logging import Formatter
import json
import pickle
import matplotlib.pyplot as plt


# logger setup
logger = logging.getLogger("main")

# create handler
handler = TimedRotatingFileHandler(
    filename='./public/main.log', when='D', interval=1, backupCount=7, encoding='utf-8', delay=False)

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
        self.base_balance = self.ftx_client.get_balance_specific(
            self.base_symbol)
        self.quote_balance = self.ftx_client.get_balance_specific(
            self.quote_symbol)
        self.init_nav = float(0 if not self.base_balance else self.base_balance['usdValue']) + float(
            0 if not self.quote_balance else self.quote_balance['usdValue'])

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
        self.trig_price_chg_thresh = float(
            config["rb"]['trig_price_chg_thresh'])
        #self.base_ratio = float(config["rb"]['base_ratio'])
        self.base_ratio_min = float(config["rb"]['base_ratio_min'])
        self.base_ratio_max = float(config["rb"]['base_ratio_max'])
        # technical analysis
        self.timeframe_rb = config["ta"]['timeframe_rb']
        self.ema1_len = int(config["ta"]['ema1_len'])
        self.ema2_len = int(config["ta"]['ema2_len'])
        self.timeframe_ratio = config["ta"]['timeframe_ratio']
        self.rsi_len = int(config["ta"]['rsi_len'])

    def update_stats(self):
        # datetime
        self.datetime = datetime.datetime.now()
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
        self.base_balance = self.ftx_client.get_balance_specific(
            self.base_symbol)
        self.quote_balance = self.ftx_client.get_balance_specific(
            self.quote_symbol)
        self.base_balance_value = float(
            0 if not self.base_balance else self.base_balance['usdValue'])
        self.quote_balance_value = float(
            0 if not self.quote_balance else self.quote_balance['usdValue'])
        self.nav = self.base_balance_value + self.quote_balance_value
        self.base_balance_value_ratio = self.base_balance_value/self.nav
        self.base_balance_value_ratio_pct = round(
            self.base_balance_value_ratio*100, 2)
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
              str(round(float(0 if not self.base_balance else self.base_balance['free']), 4)))
        print(self.quote_symbol+"_balance: " +
              str(round(float(0 if not self.quote_balance else self.quote_balance['free']), 2)))
        print("{}_ratio: {}%".format(self.base_symbol,
              self.base_balance_value_ratio_pct))
        print("price_chg: "+str(self.price_chg_pct)+"%")
        print("last_rb_price: {}".format(self.last_rb_price))
        print("last_rb_price_chg: {}%".format(self.last_rb_price_chg_pct))
        print("NAV: {}/{} [{}%]".format(round(self.nav, 2),
              round(self.init_nav, 2), round(self.nav_pct, 2)))
        print("NAV_chg: {}%".format(self.nav_pct-100))
        print("--------------------")
        print("timestamp:", self.datetime.strftime("%d/%m/%Y %H:%M:%S"))
        print("--------------------")

    def save_instance(self):
        # json
        instance = dict(self.__dict__)  # make copy of dict
        instance['ftx_client'] = str(instance['ftx_client'])
        instance['datetime'] = self.datetime.strftime("%d/%m/%Y %H:%M:%S")
        with open("./public/instance.json", "w") as file_json:
            json.dump(instance, file_json, indent=4)
        # pickle
        with open('./instance.pkl', 'wb') as file_pkl:
            pickle.dump(self, file_pkl, pickle.HIGHEST_PROTOCOL)

    def plot(self):
        # get data from CSV
        with open('./public/trade_log.csv', 'r') as read_obj:
            # pass the file object to reader() to get the reader object
            csv_reader = reader(read_obj)
            # Pass reader object to list() to get a list of lists
            data = list(csv_reader)
            del data[0]
        # plot
        time = [i[0] for i in data]
        #price = [i[1] for i in data]
        price_chg_pct = [i[2] for i in data]
        #nav = [i[3] for i in data]
        nav_chg_pct = [i[4] for i in data]
        base_ratio = [i[5] for i in data]
        fig, (ax1, ax2) = plt.subplots(2, sharex=True)
        ax1.plot(time, price_chg_pct, color="r", marker=".", label="price%")
        ax1.plot(time, nav_chg_pct, color="g", marker=".", label='nav%')
        #ax1.set_ylim(0, 500)
        ax1.legend()
        ax2.plot(time, base_ratio, marker=".", label='asset ratio%')
        ax2.set_ylim(0, 100)
        ax2.legend()
        fig.savefig("./public/trade_logs.svg")
        logger.info("saved plot => ./public/trade_logs.svg")

    def run(self):
        while True:
            try:
                # update config
                self.read_config()

                # price tick
                self.update_stats()
                self.save_instance()

                # check ta signal
                ta_rb_df = check_ta_ema(self.market_symbol, self.timeframe_rb,
                                        self.ema1_len, self.ema2_len, 100, name="rb")
                rb_sig = ta_rb_df.iloc[-2, -1]
                ta_ratio_df = check_ta_rsi(self.market_symbol, self.timeframe_ratio,
                                           self.rsi_len, 100, name="ratio")
                rsi_quote_ratio_pct = ta_ratio_df.iloc[-2, -1]
                rsi_base_ratio_pct = 100 - rsi_quote_ratio_pct
                rsi_base_ratio = rsi_base_ratio_pct/100

                logger.info(
                    "rb_sig={} | rsi_quote_ratio_pct={} | rsi_base_ratio_pct={}".format(rb_sig, rsi_quote_ratio_pct, rsi_base_ratio_pct))
                logger.info(
                    "rsi_base_ratio={} | base_balance_value_ratio={} | last_rb_price_chg_pct={} | trig_price_chg_thresh={}".format(rsi_base_ratio, self.base_balance_value_ratio, self.last_rb_price_chg_pct, self.trig_price_chg_thresh))

                # check rb
                if (rb_sig == 1 or rb_sig == 2) and rsi_base_ratio != self.base_balance_value_ratio and abs(self.last_rb_price_chg_pct) > self.trig_price_chg_thresh:
                    logger.info("execute rebalance")

                    # calculate
                    if rsi_base_ratio > self.base_ratio_max:
                        rsi_base_ratio = self.base_ratio_max
                    elif rsi_base_ratio < self.base_ratio_min:
                        rsi_base_ratio = self.base_ratio_min

                    logger.info(
                        "rsi_base_ratio_filter={} | base_ratio_max={} | base_ratio_min={}".format(rsi_base_ratio, self.base_ratio_max, self.base_ratio_min))

                    trade_val = abs((self.nav*rsi_base_ratio) -
                                    (self.nav*self.base_balance_value_ratio))
                    trade_unit = trade_val/self.price

                    logger.info(
                        "trade_val={} | trade_unit={}".format(trade_val, trade_unit))

                    # check rb buy/sell
                    traded = False
                    if self.base_balance_value_ratio > rsi_base_ratio:
                        # sell
                        instant_limit_order(
                            self.ftx_client, self.market_symbol, "sell", trade_unit)
                        traded = True

                        logger.info("sold {} {}".format(
                            trade_unit, self.base_symbol))
                    elif self.base_balance_value_ratio < rsi_base_ratio:
                        # buy
                        instant_limit_order(
                            self.ftx_client, self.market_symbol, "buy", trade_unit)
                        traded = True

                        logger.info("brought {} {}".format(
                            trade_unit, self.base_symbol))

                    # check traded
                    if traded:
                        logger.info("traded")

                        # update last_rb_price
                        self.last_rb_price = self.price
                        # re tick
                        self.update_stats()
                        self.save_instance()
                        # update log
                        add_row(self.datetime.strftime("%d/%m/%Y %H:%M:%S"),
                                self.price, self.price_chg_pct, self.nav, (self.nav_pct-100), self.base_balance_value_ratio_pct)
                        # plot
                        self.plot()

                # print stats
                self.display_stats()

            except Exception as err:
                print(err)
                logger.error(err)
            finally:
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

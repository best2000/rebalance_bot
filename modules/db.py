#import csv
import sqlite3,os

if not os.path.isfile("./public/logs/log.db"):
    conn = sqlite3.connect("./public/logs/log.db")
    conn.cursor().execute("""
          CREATE TABLE trade_logs (
                datetime int,
                price real,
                price_chg_pct real,
                nav real,
                nav_chg_pct real,
                base_ratio real
            )""")
    conn.commit()
    conn.close()

def insert_trade_log(datetime: int, price: float, price_chg: float, nav: float, nav_chg_pct: float, base_ratio_pct: float):
    conn = sqlite3.connect("./public/logs/log.db")
    conn.cursor().execute("""
              INSERT INTO trade_logs VALUES ({},{},{},{},{},{})
              """.format(datetime, price, price_chg, nav, nav_chg_pct, base_ratio_pct))
    conn.commit()
    conn.close()


def truncate_table(table: str):
    conn = sqlite3.connect("./public/logs/log.db")
    conn.cursor().execute("DELETE FROM {}".format(table))
    conn.commit()
    conn.close()




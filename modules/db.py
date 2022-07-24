#import csv
import sqlite3

from cv2 import add


def connect(db_file: str):
    conn = sqlite3.connect(db_file)
    return conn

# c.execute("""
#           CREATE TABLE trade_logs (
#                 datetime int,
#                 price real,
#                 price_chg_pct real,
#                 nav real,
#                 nav_pct real,
#                 base_ratio real
#             )""")

# col = ["datetime", "price", "price_chg%", "NAV", "NAV%", "base_ratio%"]
# with open('./public/logs/trade_log.csv', 'w', encoding='UTF8') as f:
#     writer = csv.writer(f)
#     writer.writerow(col)


def insert_trade_log(datetime: int, price: float, price_chg: float, nav: float, nav_pct: float, base_ratio_pct: float):
    conn = connect("./public/logs/log.db")
    conn.cursor().execute("""
              INSERT INTO trade_logs VALUES ({},{},{},{},{},{})
              """.format(datetime, price, price_chg, nav, nav_pct, base_ratio_pct))
    conn.commit()
    conn.close()


def truncate_table(table: str):
    conn = connect("./public/logs/log.db")
    conn.cursor().execute("DELETE FROM {}".format(table))
    conn.commit()
    conn.close()

import csv

col = ["datetime", "price", "price_chg%", "NAV", "NAV_chg%", "base_ratio%"]
with open('./public/trade_log.csv', 'w', encoding='UTF8') as f:
    writer = csv.writer(f)
    writer.writerow(col)


def add_row(datetime: str, price: float, price_chg: float, nav: float, nav_pct_chg: float, base_ratio_pct: float):
    with open('./public/trade_log.csv', 'a', encoding='UTF8') as f:
        writer = csv.writer(f)
        writer.writerow([datetime, price, price_chg,
                        nav, nav_pct_chg, base_ratio_pct])

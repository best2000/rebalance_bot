import pandas

columns = {"time": [], "symbol": [], "type": [], "asset_price": [], "price_pct_change": [], "trade_value": [],
           "asset_ratio": [], "asset_balance": [], "stable_asset_balance": [], "position_value": []}
df = pandas.DataFrame(columns)

def add_row(time: str, symbol: str, type: str, ass_price: float, asset_price_pct_change: float, trade_val: float, ass_ratio: float, ass_balance: float, sta_balance: float, pos_val: float):
    global df
    row = {"time": time, "symbol": symbol, "type": type, "asset_price": ass_price, "price_pct_change": asset_price_pct_change, "trade_value": trade_val,
           "asset_ratio": ass_ratio, "asset_balance": ass_balance, "stable_asset_balance": sta_balance, "position_value": pos_val}
    df = df.append(row, ignore_index=True)


def write_csv():
    global df
    df.to_csv("history_log.csv")


#add_row("tiejhj", "symbol", "BUY", 10.35, 15.2,102.3, 0.5, 102.69, 154.521, 156.7)
#write_csv()

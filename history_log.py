import pandas

columns = {"Time": [], "Type": [], "Asset price": [], "Trade value": [],
           "Asset ratio": [], "Asset balance": [], "Stable asset balance": [], "Position value": []}
df = pandas.DataFrame(columns)

def add_row(time: int, type: str, ass_price: float, trade_val: float, ass_ratio: float, ass_balance: float, sta_balance: float, pos_val: float):
    global df
    row = {"Time": time, "Type": type, "Asset price": ass_price, "Trade value": trade_val,
           "Asset ratio": ass_ratio, "Asset balance": ass_balance, "Stable asset balance": sta_balance, "Position value": pos_val}
    df = df.append(row, ignore_index=True)

def write_csv():
    global df
    df.to_csv("history_log.csv")


#add_row(1122312,"sell",15.21,123.0,0.5,12.0,45.0,67.0)
#print(df)
#write_csv()
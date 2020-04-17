import os
import pandas as pd
import numpy as np
from Black_Scholes import BlackScholes
import re
import datetime
import time

def change_maturity(row):
    mtr = row['Maturity']
    if mtr != "PERPETUAL":
        month_list = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        mtr = re.split('([A-Z]+)', mtr)
        month = month_list.index(mtr[1]) + 1
        maturity = datetime.date(int(mtr[2]) + 2000, month, int(mtr[0]))
        maturity = datetime.datetime.combine(maturity,datetime.time(8,0,0))
    else:
        maturity = row['timestamp']
    return maturity

def change_maturity1(mtr):
    month_list = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    mtr = re.split('([A-Z]+)', mtr)
    month = month_list.index(mtr[1]) + 1
    maturity = datetime.date(int(mtr[2]) + 2000, month, int(mtr[0]))
    maturity = datetime.datetime.combine(maturity, datetime.time(8, 0, 0))
    return maturity

def change_time(timestamp):
    timestamp = timestamp.split("T")
    time = timestamp[1].strip("Z")
    time = time.split(".")[0]
    date_str = timestamp[0] + " " + time
    new_timestamp = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    return new_timestamp

def outer_interpolation(mtr1,mtr2,price1,price2,t_mtr):
    t_price = price2 + (price2 - price1) * (t_mtr - mtr2) / (mtr2 - mtr1)
    return t_price

row_count = 0
for row_count in range(10):
    filepath = "D:\\deri-bit\\20200405"
    fileDir = os.listdir(filepath)
    option_df = pd.DataFrame()
    future_df = pd.DataFrame()

    for symbol in fileDir:
        temp_df = pd.read_csv(filepath + "/"+symbol)
        symbol_list = re.split("-", symbol)

        if (symbol_list[0] != "BTC") :
            continue

        if (len(symbol_list) == 4):
            try:
                temp_series = temp_df.iloc[row_count,:]
                temp_series['symbol'] = re.split("_", symbol)[0]
                option_df = option_df.append(temp_series)
            except IndexError:
                continue

        else:
            temp_series = temp_df.iloc[row_count,:]
            temp_series['symbol'] = re.split("_", symbol)[0]
            future_df = future_df.append(temp_series)

    option_df = option_df.loc[:, ["symbol", "timestamp", "bid1_price", "ask1_price"]]
    future_df = future_df.loc[:, ["symbol", "timestamp", "bid1_price", "ask1_price"]]


    option_df['timestamp'] = option_df['timestamp'].apply(change_time)
    option_df['Maturity'] = option_df['symbol'].apply(lambda i:i.split("-")[1])
    option_df['Maturity'] = option_df.apply(change_maturity,axis = 1)
    option_df['Strike'] = option_df['symbol'].apply(lambda i:i.split("-")[2])
    option_df['CallPut'] = option_df['symbol'].apply(lambda i:i.split("-")[3])
    future_df['timestamp'] = future_df['timestamp'].apply(change_time)
    future_df['Maturity'] = future_df['symbol'].apply(lambda i:i.split("-")[1])
    future_df['Maturity'] = future_df.apply(change_maturity,axis = 1)
    future_df['mtr'] = future_df['Maturity'] - future_df['timestamp']
    future_df['mtr'] = future_df['mtr'].apply(lambda i:i.total_seconds()/(365*24*60*60))
    future_df = future_df.sort_values('mtr')
    future_ttm = list(future_df['mtr'])
    future_price = list((future_df['bid1_price'] + future_df['ask1_price'])/2)

    time_start = time.time()
    for i in range(len(option_df)):
        one_option = option_df.iloc[i,:]
        #one_option['timestamp'] = change_time(one_option['timestamp'])
        #one_option['Maturity'] = one_option['symbol'].split("-")[1]
        #one_option['Maturity'] = change_maturity1(one_option['Maturity'])
        #one_option['Strike'] = one_option['symbol'].split("-")[2]
        #one_option['CallPut'] = one_option['symbol'].split("-")[3]
        ttm = (one_option["Maturity"] - one_option['timestamp']).total_seconds()/(365*24*60*60)
        underlying = np.interp(ttm,future_ttm,future_price)
        if ttm < max(future_ttm):
            underlying = np.interp(ttm,future_ttm,future_price)
        else:
            underlying = outer_interpolation(future_ttm[-2],future_ttm[-1], future_price[-2],future_price[-1],ttm)
        bid_price = one_option['bid1_price'] * underlying
        ask_price = one_option['ask1_price'] * underlying
        mid_price = (bid_price + ask_price) / 2
        interest =0
        strike = int(one_option['Strike'])
        optiontype = one_option['CallPut']
        if (bid_price ==0 or ask_price == 0):
            implied_vol = 0
        else:
            b_s = BlackScholes(underlying,0,0,ttm)
            implied_vol = b_s.BS_impliedVol(strike,mid_price, optiontype)

    time_end = time.time()
    time_c = time_end- time_start
    print("finish one time "+str(time_c))




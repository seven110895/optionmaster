import os
import pandas as pd
import re
import datetime
import h5py
import numpy as np
from pandas.io import sql
from sqlalchemy import create_engine
import datetime, time
import pymysql
import matplotlib.pyplot as plt
from change_directory import directory
from matplotlib.backends.backend_pdf import PdfPages
from get_realtime_data import get_realtime_data

def change_maturity(mtr):
    month_list = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    mtr = re.split('([A-Z]+)', mtr)
    month = month_list.index(mtr[1]) + 1
    maturity = datetime.date(int(mtr[2]) + 2000, month, int(mtr[0]))
    return maturity

def find_maturity(row):
    ATM_df = pd.read_csv("D:\\optionmaster\\Trade_plot\\ATM_information.csv")
    temp_df = ATM_df.loc[ATM_df['Date'] == str(row['Date']), :]
    temp_df = temp_df.loc[temp_df['Maturity'] == str(row['Maturity']), :]
    underlying = temp_df['underlying_price']
    return float(underlying)

def get_trade_hour(timestamp):
    timestamp_list = timestamp.split('T')
    time = timestamp_list[1].strip('Z').split(':')
    hour = int(time[0])
    return hour

def get_trade_data(instrument_list,date):
    df_list = []
    for i in instrument_list:
        symbol_list = i.split('-')
        if len(symbol_list) != 4 or symbol_list[0] != 'BTC':
            pass
        else:
            temp_dic = 'Y:/deribit/trade/' + i + '/' + i + '_' + str(date).replace('-','') + '.h5'
            try:
                with h5py.File(temp_dic, 'r') as f:
                    temp = pd.DataFrame(np.array(f[i]))
                    temp['instrument'] = i
                    temp_result = temp[['timestamp', 'price', 'size','instrument']]
                    temp_result['timestamp'] = temp_result['timestamp'].apply(lambda i: datetime.datetime.fromtimestamp(i/1000))
                    temp_result.columns = ['timestamp','price','quantity','instrument']
                    df_list.append(temp_result)
            except OSError:
                pass
    df = df_list[0].append(df_list[1:])
    return df

def get_daily_trade(date):
    server = '192.168.50.135'
    user = 'share'
    passwd = 'public@MC123'
    db_conn = create_engine(f'mysql+pymysql://{user}:{passwd}@{server}/datacenter')
    df_trades = pd.read_sql('SELECT * FROM trades_DE', con=db_conn)
    df_trades['timestamp'] = df_trades['timestamp'].apply(
        lambda i: datetime.datetime.fromtimestamp(i / 1000))
    #df_trades['timestamp'] = df_trades['timestamp'].apply( lambda i: i- datetime.timedelta(hours= 8))
    date = datetime.datetime.combine(date,datetime.time(0,0,0))
    date_2 = date + datetime.timedelta(days=1)
    date_2 = datetime.datetime.combine(date_2,datetime.time(0,0,0))
    df_trades = df_trades[df_trades['timestamp'] > date]
    df_trades = df_trades[df_trades['timestamp'] < date_2]
    option_trade_df = df_trades.copy()
    option_trade_df['CallPut'] = option_trade_df['symbol'].apply(lambda x:x.split('-')[3])
    option_trade_df['Strike'] = option_trade_df['symbol'].apply(lambda x:int(x.split('-')[2]))
    option_trade_df['Maturity'] = option_trade_df['symbol'].apply(lambda x:x.split('-')[1])
    option_trade_df['Maturity'] = option_trade_df['Maturity'].apply(change_maturity)
    option_trade_df['Currency'] =  option_trade_df['symbol'].apply(lambda x:x.split('-')[0])
    option_trade_df['Trade_Hour'] = option_trade_df['timestamp'].apply(lambda x:x.hour)
    option_trade_df = option_trade_df[option_trade_df['Currency'] == "BTC"]
    return option_trade_df


date = datetime.date.today() - datetime.timedelta(days = 1)
option_trade_df = get_daily_trade(date)
a =  option_trade_df.groupby(['Maturity']).agg({'quantity':'sum'})
agg_df = option_trade_df.groupby(['Maturity', 'Strike', 'Trade_Hour']).agg({'quantity':'sum'})
agg_df = agg_df.reset_index()
mtr_agg_df = agg_df.groupby('Maturity')
writer = pd.ExcelWriter('D:\\optionmaster/Trade_plot/Daily_Trade_Volume/' + str(datetime.date.today()) + '_Trade_Volume.xlsx')

for mtr, mtr_group in mtr_agg_df:
    Trade_df = mtr_group.pivot(index = 'Strike', columns = 'Trade_Hour', values = 'quantity')
    Trade_df = Trade_df.fillna(0)
    Trade_df.loc['All_strike', :] = Trade_df.sum()
    Trade_df_pct = Trade_df.div(Trade_df.sum(axis=1), axis=0)
    Trade_df_pct = Trade_df_pct.reset_index()
    Trade_df_pct.to_excel(writer, sheet_name=str(mtr), index=False)

All_maturity = option_trade_df.groupby(['Trade_Hour']).agg({'quantity':'sum'})
all_df = All_maturity.reset_index()
all_df['Pct'] = all_df['quantity'] / sum(all_df['quantity'])

for i in range(5):
    temp_option_trade_df = get_daily_trade(date - datetime.timedelta(days= i+1))
    temp_all_maturity_df = temp_option_trade_df.groupby(['Trade_Hour']).agg({'quantity':'sum'})

    temp_all_df = temp_all_maturity_df.reset_index()
    temp_all_df.columns = ['Trade_Hour', 'quantity_'+ str(i+1)]
    all_df = pd.merge(all_df, temp_all_df, how='left')

for avg in [1,3,5]:
    all_df['Past_' + str(avg) + '_day_avg'] = all_df.apply(lambda x: np.average(x[3:3+avg]),axis = 1)
    all_df['Pct_' + str(avg)] = all_df['Past_' + str(avg) + '_day_avg'] / sum(all_df['Past_' + str(avg) + '_day_avg'])

total_df = all_df.loc[:,['Trade_Hour', 'quantity', 'Pct', 'Past_1_day_avg', 'Pct_1', 'Past_3_day_avg', 'Pct_3', 'Past_5_day_avg', 'Pct_5']]
total_df.loc['Total',:] = total_df.sum(axis=0)
total_df.loc['Total','Trade_Hour'] = 'Total'
total_df.to_excel(writer, sheet_name='All_Trade_Volume', index=False)
writer.save()
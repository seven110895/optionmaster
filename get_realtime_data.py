import re
import datetime
import pandas as pd
import h5py
import numpy as np
import os

class get_realtime_data:
    def get_ticker_df(self,h5file):
        df_list = []
        with h5py.File(h5file, 'r') as f:
            allsymbols = f.keys()
            # print(allsymbols)
            for symbol in allsymbols:
                symbol_list = symbol.split('-')
                if len(symbol_list) != 4 or symbol_list[0] != 'BTC':
                    pass
                else:
                    df = pd.DataFrame(np.array(f[symbol]))
                    df['symbol'] = symbol
                    df_list.append(df)
        df = df_list[0].append(df_list[1:])
        return df

    def change_maturity(self,mtr):
        month_list = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        mtr = re.split('([A-Z]+)', mtr)
        month = month_list.index(mtr[1]) + 1
        maturity = datetime.date(int(mtr[2]) + 2000, month, int(mtr[0]))
        return maturity

    def get_ticker_new_df(self, date):
        symbol_list = os.listdir("Y:\\deribit\\ticker")
        df_list = []
        for i in symbol_list:
            if len(symbol_list) != 4 or symbol_list[0] != 'BTC':
                continue
            else:
                try:
                    h5file = "Y:\\deribit\\ticker/" + i + '/' + i + '_' + str(date).replace('-','') + '.h5'
                    f = h5py.File(h5file, 'r')
                    df = pd.DataFrame(np.array(f[i]))
                    df['symbol'] = i
                    df_list.append(df)
                except:
                    continue
            df = df_list[0].append(df_list[1:])
        return df


    def get_realtime_orderbook(self, date):
        date_str = date
        date_str = str(date_str).replace("-", "")
        h5file = "X:\\SG\\deribit\\DERIBIT_"+date_str +"_ticker.h5"
        #h5file = 'Y:/deribit/ticker_old/DERIBIT_' + date_str +'.h5ticker'
        option_df = self.get_ticker_df(h5file)
        option_df['timestamp'] = option_df['timestamp'].apply(lambda i: datetime.datetime.fromtimestamp(i/1000)- datetime.timedelta(hours= 8))
        option_df['Maturity'] = option_df['symbol'].apply(lambda x: x.split('-')[1])
        option_df['Maturity'] = option_df['Maturity'].apply(self.change_maturity)
        option_df['Strike'] = option_df['symbol'].apply(lambda x: int(x.split('-')[2]))
        option_df['CallPut'] = option_df['symbol'].apply(lambda x: x.split('-')[3])

        option_df_new = option_df.loc[:, ['symbol', 'timestamp', 'Maturity','Strike', 'CallPut', 'underlying_index', 'underlying_price',
                                          'best_bid_price', 'bid_iv', 'best_ask_price', 'ask_iv', 'mark_price', 'mark_iv', 'delta']]

        return option_df_new

    def get_tradetime_vol(self, dailytradetime, delta_T):
        delayTradeTime = dailytradetime + datetime.timedelta(minutes=delta_T)
        previousTradeTime = dailytradetime - datetime.timedelta(minutes=delta_T)
        option_df = self.get_realtime_orderbook(dailytradetime.date())
        option_df_by_symbol = option_df.groupby('symbol')
        symbol_count = 0
        all_data = pd.DataFrame()
        for symbol, symbol_group in option_df_by_symbol:
            data_1_time = symbol_group['timestamp']
            option_count = 0
            for t_count in range(0, len(data_1_time)):
                t = data_1_time[t_count]
                if previousTradeTime <= t <= delayTradeTime:
                    option_count = t_count
                    break
            start_t = data_1_time[option_count]
            if option_count == 0 and (start_t < previousTradeTime or start_t > delayTradeTime):
                continue
            if symbol_count == 0 :
                all_data = pd.DataFrame(columns = symbol_group.columns)
                all_data.loc[symbol_count, :] = symbol_group.loc[option_count, :]
            else:
                all_data.loc[symbol_count, :] = symbol_group.loc[option_count, :]
            symbol_count += 1
        return all_data



#ss = get_realtime_data()
#option_df = ss.get_realtime_orderbook()
#option_df = option_df.sort_values(['symbol','timestamp'])






import datetime
import pandas as pd
from get_realtime_data import get_realtime_data
import numpy as np
import uuid,json,time
from collections import defaultdict
import pandas as pd
import asyncio, websockets, requests

def ValueType_define(row):
    if row['CallPut'] == 'C':
        if row['Strike'] < row['underlying_price']:
            money_type = 'ITM'
        elif row['Strike'] > row['underlying_price']:
            money_type = 'OTM'
        else:
            money_type = 'ATM'
    else:
        if row['Strike'] < row['underlying_price']:
            money_type = 'OTM'
        elif row['Strike'] > row['underlying_price']:
            money_type = 'ITM'
        else:
            money_type = 'ATM'
    return money_type

def get_vol_list(time_record):
    date = datetime.date.today() - datetime.timedelta(days = 3)
    realtime_dir = get_realtime_data()
    realtime_all_mtr_options = realtime_dir.get_realtime_orderbook(date)
    realtime_all_mtr_options['ValueType'] = realtime_all_mtr_options.apply(ValueType_define,axis=1)
    OTM_all_mtr_options = realtime_all_mtr_options[realtime_all_mtr_options['ValueType'] == 'OTM']
    one_day_options = OTM_all_mtr_options[OTM_all_mtr_options['Maturity'] == datetime.date(2020,3,13)]

    strike_list = list(set(one_day_options['Strike']))
    strike_list.sort()
    bid_vol, ask_vol, mid_vol = [], [], []
    for i in strike_list:
        strike_df = one_day_options[one_day_options['Strike'] == i]
        timestamp = list(strike_df['timestamp'])
        strike_bid_vol = list(strike_df['bid_iv'])
        strike_ask_vol = list(strike_df['ask_iv'])
        strike_mid_vol = list(strike_df['mark_iv'])

        option_count = 0
        for t_count in range(0, len(timestamp)):
            t = timestamp[t_count]
            if t <= time_record:
                option_count = t_count
            else:
                break
        bid_vol.append(strike_bid_vol[option_count] if strike_bid_vol[option_count] > 0 else np.nan )
        ask_vol.append(strike_ask_vol[option_count] if strike_ask_vol[option_count] > 0 else np.nan )
        mid_vol.append(strike_mid_vol[option_count] if strike_mid_vol[option_count] > 0 else np.nan )
    return bid_vol,ask_vol,mid_vol,strike_list




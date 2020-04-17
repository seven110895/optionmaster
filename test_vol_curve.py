import matplotlib.pyplot as plt
import time
import numpy as np
from get_realtime_data import get_realtime_data
import datetime


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


date = datetime.date.today() - datetime.timedelta(days = 2)
realtime_dir = get_realtime_data()
realtime_all_mtr_options = realtime_dir.get_realtime_orderbook(date)
realtime_all_mtr_options['ValueType'] = realtime_all_mtr_options.apply(ValueType_define,axis=1)
OTM_all_mtr_options = realtime_all_mtr_options[realtime_all_mtr_options['ValueType'] == 'OTM']
all_mtr_options = OTM_all_mtr_options.groupby('Maturity')
mtr_list = list(set(OTM_all_mtr_options['Maturity']))
plt.ion()
plt.rcParams['figure.figsize'] = (12, 12)
time_record = datetime.datetime(2020,3,7,15,18,0)
while time_record < max(OTM_all_mtr_options['timestamp']):
    plt.clf()
    plt.suptitle('Time:' + str(time_record),fontsize = 12,y=1)
    mtr_count = 0
    for mtr, mtr_group in all_mtr_options:
        strike_list = list(set(mtr_group['Strike']))
        strike_list.sort()
        bid_vol, ask_vol, mid_vol = [], [], []
        for i in strike_list:
            strike_df = mtr_group[mtr_group['Strike'] == i]
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
        mtr_graph = plt.subplot(4, 2, mtr_count + 1)
        mtr_graph.set_title('Maturity:' + str(mtr))
        mtr_graph.set_xlabel('Strike')
        mtr_graph.set_ylabel('Vol')
        mtr_graph.plot(strike_list, bid_vol, '.-', label = 'bid_vol')
        mtr_graph.plot(strike_list, ask_vol, '.-', label='ask_vol')
        mtr_graph.plot(strike_list, mid_vol, '.-', label='mid_vol')
        mtr_graph.legend(loc='best')
        mtr_count += 1
    plt.tight_layout()
    plt.pause(5)
    time_record = time_record + datetime.timedelta(seconds= 5)
plt.ioff()
plt.show()






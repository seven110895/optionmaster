import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from data_clean import straddle_prepare
from data_clean import option_data
from change_directory import directory

project_dir = directory()
option_data = option_data()
tradeHour = datetime.time(16, 0, 0)
delta_T = 1     # minute
dateList = option_data.get_perp_date_list()
startDate = min(dateList)
endDate = max(dateList) + datetime.timedelta(days=1)
option_file_df = option_data.get_option_df()
option_file_by_date = option_file_df.groupby('Date')
day_count = 0
total_data = pd.DataFrame(columns=('Time', 'Underlying', 'Weight_1', 'Weight_2', 'Strike', 'Maturity_1', 'Maturity_2',
                                   'Sell_Bid_1_Call', 'Sell_Bid_1_Put', 'Sell_Ask_1_Call', 'Sell_Ask_1_Put',
                                   'Sell_Bid_2_Call', 'Sell_Bid_2_Put', 'Sell_Ask_2_Call', 'Sell_Ask_2_Put',
                                   'Buy_Bid_1_Call', 'Buy_Bid_1_Put', 'Buy_Ask_1_Call', 'Buy_Ask_1_Put',
                                   'Buy_Bid_2_Call', 'Buy_Bid_2_Put', 'Buy_Ask_2_Call', 'Buy_Ask_2_Put',
                                   'net_pos', 'cash_balance', 'Daily_Return', 'Cost'))
total_data.loc[0, :] = [0 for _ in range(total_data.shape[1])]

for d in np.arange(startDate, endDate):
    dailyTradeTime = datetime.datetime.combine(np.datetime64(d).astype(datetime.date), tradeHour)
    current_day_options = option_file_by_date.get_group(d)
    current_day_options = current_day_options.sort_values(by='Maturity')
    mtr_options = current_day_options.groupby('Maturity')
    straddle_pre = straddle_prepare(current_day_options, tradeHour, d, delta_T)
    perp_underlying = straddle_pre.get_perp_price()
    if d in dateList:
        if day_count == 0:
            temp_return = total_data.loc[0,:]
        else :
            temp_return = total_data.loc[day_count-1,:]

        ## 决定是否调仓的信号，之后具体定义
        iv = 5
        new_net_pos, signal = straddle_pre.get_signal_pos(temp_return.loc['net_pos'], iv)

        if signal != "hold":
            weight_mtr_list = [0 for _ in range(5)]
            buy_list = [0 for _ in range(8)]
            sell_list = [0 for _ in range(8)]
            d_cash, d_return, cost = 0, 0, 0
            option_mtr_weight = straddle_pre.get_all_options_info()
            d1_bid, d1_ask = straddle_pre.get_bid_ask_price(option_mtr_weight[2], option_mtr_weight[3], 0)
            d2_bid, d2_ask = straddle_pre.get_bid_ask_price(option_mtr_weight[2], option_mtr_weight[4], 0)

            if signal == "long":
                buy_list = d1_bid + d1_ask + d2_bid + d2_ask
                weight_mtr_list = option_mtr_weight
                cost = option_data.trade_cost(d1_bid, d1_ask, option_mtr_weight[0], 0)\
                    + option_data.trade_cost(d2_bid, d2_ask, option_mtr_weight[1], 0)
                d_cash = straddle_pre.calculate_cash(d1_bid, d1_ask, d2_bid, d2_ask,
                                                     option_mtr_weight[0], option_mtr_weight[1], 0)

            # clean means close the long position
            elif signal == "clean":
                buy_list = temp_return.loc['Buy_Bid_1_Call':'Buy_Ask_2_Put']
                weight_mtr_list = temp_return.loc['Weight_1':'Maturity_2']
                sell_list = d1_bid + d1_ask + d2_bid + d2_ask

                cost = option_data.trade_cost(d1_bid, d1_ask, temp_return['Weight_1'], 0)\
                    + option_data.trade_cost(d2_bid, d2_ask, temp_return['Weight_2'], 0)
                d_cash = temp_return['cash_balance'] \
                    + straddle_pre.calculate_cash(d1_bid, d1_ask, d2_bid, d2_ask,
                                                  option_mtr_weight[0], option_mtr_weight[1], 1)
                d_return = d_cash
                d_cash = 0

            # clean_long means close the original long position and open a new long position
            elif signal == "clean_long":
                buy_list = d1_bid + d1_ask + d2_bid + d2_ask
                sell_list = d1_bid + d1_ask + d2_bid + d2_ask
                weight_mtr_list = option_mtr_weight
                cost = option_data.trade_cost(d1_bid, d1_ask, option_mtr_weight[0], 0)\
                    + option_data.trade_cost(d2_bid, d2_ask, option_mtr_weight[1], 0)\
                    + option_data.trade_cost(d1_bid, d1_ask, temp_return['Weight_1'], 1)\
                    + option_data.trade_cost(d2_bid, d2_ask, temp_return['Weight_2'], 1)
                d_return = temp_return['cash_balance'] \
                    + straddle_pre.calculate_cash(d1_bid, d1_ask, d2_bid, d2_ask,
                                                  temp_return.loc['Weight_1'], temp_return.loc['Weight_2'], 1)
                d_cash = straddle_pre.calculate_cash(d1_bid, d1_ask, d2_bid, d2_ask,
                                                     option_mtr_weight[0], option_mtr_weight[1], 0)
            temp_return = [dailyTradeTime, perp_underlying] + weight_mtr_list + sell_list + buy_list \
                + [new_net_pos, d_cash, d_return, cost]
            total_data.loc[day_count, :] = temp_return
        else:
            total_data.loc[day_count, :] = temp_return
            total_data.loc[day_count, 'Time':'Underlying'] = [dailyTradeTime, perp_underlying]
    day_count += 1

total_data['cumulative_return'] = np.cumsum(total_data['Daily_Return'])
plt.plot(total_data['Time'], total_data['cumulative_return'])
plt.show()














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
                                   'net_pos', 'cash_balance', 'Daily_Return', 'Cost', 'signal', 'Op_delta','daily_hedge_pos','hedge_future_price','hedge_cost','cum_hedge_cash','realized_hedge_return'))
total_data.loc[0, :] = [0 for _ in range(total_data.shape[1])]

historical_vol = pd.read_csv("D:/optionmaster/Straddle/Straddle_vol/Dec_atm.csv")

startDate = datetime.date(2019,12, 1)
endDate  = datetime.date(2019,12, 31)
for d in np.arange(startDate, endDate):
    if d in dateList:
        dailyTradeTime = datetime.datetime.combine(np.datetime64(d).astype(datetime.date), tradeHour)
        current_day_options = option_file_by_date.get_group(d)
        current_day_options = current_day_options.sort_values(by='Maturity')
        mtr_options = current_day_options.groupby('Maturity')
        straddle_pre = straddle_prepare(current_day_options, tradeHour, d, delta_T)

        current_day_vol_df = historical_vol.loc[historical_vol['Date'] == str(d), :]
        current_day_vol_df = current_day_vol_df.sort_values(['Maturity', 'CallPut'])
        perp_underlying = straddle_pre.get_perp_price()
        if day_count == 0:
            temp_return = total_data.loc[0,:]
        else :
            temp_return = total_data.loc[day_count-1,:]


        ## 决定是否调仓的信号，之后具体定义
        option_mtr_weight = straddle_pre.get_all_options_info()
        change_contract = ([temp_return['Maturity_1'], temp_return['Maturity_2']] == [option_mtr_weight[3],option_mtr_weight[4]])
        past_delta = sum(current_day_vol_df.loc[current_day_vol_df['Maturity'] == str(temp_return['Maturity_1']), 'm_delta']) * \
                temp_return['Weight_1'] + sum(current_day_vol_df.loc[current_day_vol_df['Maturity'] == str(temp_return['Maturity_2']), 'm_delta']) * temp_return['Weight_2']

        new_delta = sum(current_day_vol_df.loc[current_day_vol_df['Maturity'] == str(option_mtr_weight[3]), 'm_delta']) * \
                 option_mtr_weight[0] + sum(current_day_vol_df.loc[current_day_vol_df['Maturity'] == str(option_mtr_weight[4]), 'm_delta']) * option_mtr_weight[1]

        new_net_pos, signal = straddle_pre.get_signal_pos(temp_return.loc['net_pos'], new_delta, past_delta, change_contract)
        
        if signal != "hold":
            weight_mtr_list = [0 for _ in range(5)]
            buy_list = [0 for _ in range(8)]
            sell_list = [0 for _ in range(8)]
            d_cash, d_return, cost = 0, 0, 0
            d1_bid = list(current_day_vol_df.loc[current_day_vol_df['Maturity'] == str(option_mtr_weight[3]),'m_bid'])
            d1_ask = list(current_day_vol_df.loc[current_day_vol_df['Maturity'] == str(option_mtr_weight[3]),'m_ask'])
            d2_bid = list(current_day_vol_df.loc[current_day_vol_df['Maturity'] == str(option_mtr_weight[4]),'m_bid'])
            d2_ask = list(current_day_vol_df.loc[current_day_vol_df['Maturity'] == str(option_mtr_weight[4]),'m_ask'])

            d1_bid_p = list(current_day_vol_df.loc[current_day_vol_df['Maturity'] == str(temp_return['Maturity_1']), 'm_bid'])
            d1_ask_p = list(current_day_vol_df.loc[current_day_vol_df['Maturity'] == str(temp_return['Maturity_1']), 'm_ask'])
            d2_bid_p = list(current_day_vol_df.loc[current_day_vol_df['Maturity'] == str(temp_return['Maturity_2']), 'm_bid'])
            d2_ask_p = list(current_day_vol_df.loc[current_day_vol_df['Maturity'] == str(temp_return['Maturity_2']), 'm_ask'])

            if signal == "long":
                buy_list = d1_bid + d1_ask + d2_bid + d2_ask
                weight_mtr_list = option_mtr_weight
                cost = option_data.trade_cost(d1_bid, d1_ask, option_mtr_weight[0], 0)\
                    + option_data.trade_cost(d2_bid, d2_ask, option_mtr_weight[1], 0)
                d_cash = straddle_pre.calculate_cash(d1_bid, d1_ask, d2_bid, d2_ask,
                                                     option_mtr_weight[0], option_mtr_weight[1], 0)
                # delta hedge param
                Op_delta = new_delta
                hedge_future_price = np.mean(current_day_vol_df.loc[current_day_vol_df['Maturity'] == str(option_mtr_weight[4]),
                                                            'hedge_future_price'])
                daily_hedge_pos = -Op_delta
                hedge_cost = abs(0.0005 * daily_hedge_pos)   # debited in BTC
                cum_hedge_cash = - hedge_future_price * daily_hedge_pos
                realized_hedge_return = 0

            # clean means close the long position
            elif signal == "clean":
                buy_list = list(temp_return.loc['Buy_Bid_1_Call':'Buy_Ask_2_Put'])
                #weight_mtr_list = list(temp_return.loc['Weight_1':'Maturity_2'])
                sell_list = d1_bid + d1_ask + d2_bid + d2_ask

                cost = option_data.trade_cost(d1_bid_p, d1_ask_p, temp_return['Weight_1'], 0)\
                    + option_data.trade_cost(d2_bid_p, d2_ask_p, temp_return['Weight_2'], 0)
                d_cash = temp_return['cash_balance'] \
                    + straddle_pre.calculate_cash(d1_bid_p, d1_ask_p, d2_bid_p, d2_ask_p,
                                                  temp_return['Weight_1'], temp_return['Weight_2'], 1)
                d_return = d_cash
                d_cash = 0
                # delta hedge param
                Op_delta = 0
                hedge_future_price = np.mean(current_day_vol_df.loc[current_day_vol_df['Maturity'] == str(temp_return['Maturity_2']),
                                                            'hedge_future_price'])
                daily_hedge_pos = - (Op_delta - temp_return['Op_delta'])
                hedge_cost = abs(0.0005 * daily_hedge_pos)
                cum_hedge_cash = (- hedge_future_price * daily_hedge_pos) + temp_return['cum_hedge_cash']
                realized_hedge_return = cum_hedge_cash / hedge_future_price

            # clean_long means close the original long position and open a new long position
            elif signal == "clean_long":
                buy_list = d1_bid + d1_ask + d2_bid + d2_ask
                sell_list = d1_bid + d1_ask + d2_bid + d2_ask
                weight_mtr_list = option_mtr_weight
                cost = option_data.trade_cost(d1_bid, d1_ask, option_mtr_weight[0], 0)\
                    + option_data.trade_cost(d2_bid, d2_ask, option_mtr_weight[1], 0)\
                    + option_data.trade_cost(d1_bid_p, d1_ask_p, temp_return['Weight_1'], 1)\
                    + option_data.trade_cost(d2_bid_p, d2_ask_p, temp_return['Weight_2'], 1)
                d_return = temp_return['cash_balance'] \
                    + straddle_pre.calculate_cash(d1_bid_p, d1_ask_p, d2_bid_p, d2_ask_p,
                                                  temp_return.loc['Weight_1'], temp_return.loc['Weight_2'], 1)
                d_cash = straddle_pre.calculate_cash(d1_bid, d1_ask, d2_bid, d2_ask,
                                                     option_mtr_weight[0], option_mtr_weight[1], 0)

                 # firstly close the old position hedging
                Op_delta = 0
                hedge_future_price = np.mean(current_day_vol_df.loc[current_day_vol_df['Maturity'] == str(temp_return['Maturity_2']),
                                                                    'hedge_future_price'])
                daily_hedge_pos = - (Op_delta - temp_return['Op_delta'])
                hedge_cost = abs(0.0005 * daily_hedge_pos)
                cum_hedge_cash = (- hedge_future_price * daily_hedge_pos) + temp_return['cum_hedge_cash']
                realized_hedge_return = cum_hedge_cash / hedge_future_price

                # then open the new position hedging
                Op_delta = new_delta
                daily_hedge_pos = - Op_delta
                hedge_cost += abs(0.0005 * daily_hedge_pos)
                cum_hedge_cash = - hedge_future_price * daily_hedge_pos

            temp_return = [dailyTradeTime, perp_underlying] + weight_mtr_list + sell_list + buy_list \
                + [new_net_pos, d_cash, d_return, cost, signal] + [Op_delta, daily_hedge_pos, hedge_future_price, hedge_cost, cum_hedge_cash, realized_hedge_return ]
            total_data.loc[day_count, :] = temp_return
        else:
            Op_delta = past_delta
            daily_hedge_pos = - (Op_delta - temp_return['Op_delta'])
            hedge_future_price = np.mean( current_day_vol_df.loc[current_day_vol_df['Maturity'] == str(temp_return['Maturity_2']),
                                                                 'hedge_future_price'])
            hedge_cost = abs(0.0005 * daily_hedge_pos)
            cum_hedge_cash = (- hedge_future_price * daily_hedge_pos) + temp_return['cum_hedge_cash']
            realized_hedge_return = 0
            total_data.loc[day_count, :] = temp_return
            total_data.loc[day_count, 'Time':'Underlying'] = [dailyTradeTime, perp_underlying]
            total_data.loc[day_count, 'signal':'realized_hedge_return'] = [signal, Op_delta, daily_hedge_pos, hedge_future_price, hedge_cost, cum_hedge_cash, realized_hedge_return ]
        day_count += 1

total_data['cumulative_return'] = np.cumsum(total_data['Daily_Return'])
plt.plot(total_data['Time'], total_data['cumulative_return'])
plt.show()
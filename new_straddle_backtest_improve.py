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
delta_T = datetime.time(15, 59, 0)
dateList = option_data.get_perp_date_list()
startDate = min(dateList)
endDate = max(dateList) + datetime.timedelta(days=1)
option_file_df = option_data.get_option_df()
option_file_by_date = option_file_df.groupby('Date')

timestamp, daily_weight_Q, daily_weight_N = [], [], []
daily_strike, daily_underlying = [], []
sell_bid_Q_1, sell_ask_Q_1, sell_bid_N_1, sell_ask_N_1, buy_bid_Q_1, buy_ask_Q_1, buy_bid_N_1, buy_ask_N_1 = \
    [], [], [], [], [], [], [], []
sell_bid_Q_2, sell_ask_Q_2, sell_bid_N_2, sell_ask_N_2, buy_bid_Q_2, buy_ask_Q_2, buy_bid_N_2, buy_ask_N_2 = \
    [], [], [], [], [], [], [], []
daily_return, cumulative_return = [], []
daily_1_maturity, daily_2_maturity = [], []
net_pos_list,cash_balance,cost_list = [], [], []
day_count = 0

for d in np.arange(startDate, endDate):
    dailyTradeTime = datetime.datetime.combine(np.datetime64(d).astype(datetime.date), tradeHour)
    current_day_options = option_file_by_date.get_group(d)
    current_day_options = current_day_options.sort_values(by='Maturity')
    mtr_options = current_day_options.groupby('Maturity')

    straddle_pre = straddle_prepare(current_day_options, tradeHour, d, delta_T)

    if d in dateList:
        perp_underlying,ATM_strike = 0, 0
        weight_1, weight_2, Maturity_1, Maturity_2, cost= 0, 0, 0, 0, 0
        temp_sell_bid_Q_1, temp_sell_ask_Q_1, temp_sell_bid_N_1, temp_sell_ask_N_1, temp_buy_bid_Q_1, temp_buy_ask_Q_1, temp_buy_bid_N_1, temp_buy_ask_N_1 = 0,0,0,0,0,0,0,0
        temp_sell_bid_Q_2, temp_sell_ask_Q_2, temp_sell_bid_N_2, temp_sell_ask_N_2, temp_buy_bid_Q_2, temp_buy_ask_Q_2, temp_buy_bid_N_2, temp_buy_ask_N_2 = 0,0,0,0,0,0,0,0
        d_return = 0
        if day_count == 0:
            net_pos = 0
            d_cash = 0

        else :
            net_pos = net_pos_list[day_count-1]
            d_cash = cash_balance[day_count-1]

        ## 决定是否调仓的信号，之后具体定义
        iv = 5
        new_net_pos,signal = straddle_pre.get_signal_pos(net_pos,iv)

        if signal != "hold" :
            perp_underlying = straddle_pre.get_underlying_price(dateList)
            # find one <30 days and one >30 days maturity
            firstMtr, secondMtr = straddle_pre.get_maturity(30)

            # linear weight
            first_weight, second_weight = straddle_pre.get_weight(firstMtr, secondMtr)

            # get ATM_strike and ATM options
            ATM_strike = straddle_pre.get_ATM_strike(perp_underlying)
            first_mtr_options = mtr_options.get_group(firstMtr)
            second_mtr_options = mtr_options.get_group(secondMtr)
            first_options = first_mtr_options.groupby('Strike').get_group(ATM_strike)
            first_options = first_options.sort_values(by='CallPut')
            second_options = second_mtr_options.groupby('Strike').get_group(ATM_strike)
            second_options = second_options.sort_values(by='CallPut')

            # get the bid ask price
            file_1 = first_options['File']
            file_2 = second_options['File']
            d1_bid, d1_ask = straddle_pre.get_bid_ask_price(file_1)
            d2_bid, d2_ask = straddle_pre.get_bid_ask_price(file_2)

            if signal == "long":
                temp_buy_bid_Q_1, temp_buy_ask_Q_1, temp_buy_bid_N_1, temp_buy_ask_N_1 = d1_bid[0],d1_ask[0],d2_bid[0],d2_ask[0]
                temp_buy_bid_Q_2, temp_buy_ask_Q_2, temp_buy_bid_N_2, temp_buy_ask_N_2 = d1_bid[1],d1_ask[1],d2_bid[1],d2_ask[1]
                weight_1,weight_2,Maturity_1,Maturity_2 = first_weight,second_weight,firstMtr,secondMtr
                cost = option_data.trade_cost(d1_bid,d1_ask,first_weight,0)+option_data.trade_cost(d2_bid,d2_ask,second_weight,0)
                d_cash  = straddle_pre.calculate_cash(d1_bid,d1_ask,d2_bid,d2_ask,weight_1,weight_2,0)

            # clean means close the long position
            elif signal == "clean":
                temp_buy_bid_Q_1, temp_buy_ask_Q_1, temp_buy_bid_N_1, temp_buy_ask_N_1 = \
                    buy_bid_Q_1[day_count-1], buy_ask_Q_1[day_count-1], buy_bid_N_1[day_count-1], buy_ask_N_1[day_count-1]
                temp_buy_bid_Q_2, temp_buy_ask_Q_2, temp_buy_bid_N_2, temp_buy_ask_N_2 = \
                    buy_bid_Q_2[day_count-1], buy_ask_Q_2[day_count-1], buy_bid_N_2[day_count-1], buy_ask_N_2[day_count-1]

                temp_sell_bid_Q_1, temp_sell_ask_Q_1, temp_sell_bid_N_1, temp_sell_ask_N_1 = d1_bid[0],d1_ask[0],d2_bid[0],d2_ask[0]
                temp_sell_bid_Q_2, temp_sell_ask_Q_2, temp_sell_bid_N_2, temp_sell_ask_N_2 = d1_bid[1],d1_ask[1],d2_bid[1],d2_ask[1]
                weight_1, weight_2 = daily_weight_Q[day_count-1], daily_weight_N[day_count-1]
                Maturity_1,Maturity_2 = daily_1_maturity[day_count-1],daily_2_maturity[day_count-1]
                cost = option_data.trade_cost(d1_bid,d1_ask,first_weight,0)+option_data.trade_cost(d2_bid,d2_ask,second_weight,0)
                d_cash += straddle_pre.calculate_cash(d1_bid,d1_ask,d2_bid,d2_ask,weight_1,weight_2,1)
                d_return = d_cash
                d_cash = 0

            # clean_long means close the original long position and open a new long position
            elif signal == "clean_long":
                temp_buy_bid_Q_1, temp_buy_ask_Q_1, temp_buy_bid_N_1, temp_buy_ask_N_1 = d1_bid[0], d1_ask[0], d2_bid[0], d2_ask[0]
                temp_buy_bid_Q_2, temp_buy_ask_Q_2, temp_buy_bid_N_2, temp_buy_ask_N_2 = d1_bid[1], d1_ask[1], d2_bid[1], d2_ask[1]
                temp_sell_bid_Q_1, temp_sell_ask_Q_1, temp_sell_bid_N_1, temp_sell_ask_N_1 = d1_bid[0], d1_ask[0], d2_bid[0], d2_ask[0]
                temp_sell_bid_Q_2, temp_sell_ask_Q_2, temp_sell_bid_N_2, temp_sell_ask_N_2 = d1_bid[1], d1_ask[1], d2_bid[1], d2_ask[1]
                weight_1, weight_2, Maturity_1, Maturity_2 = first_weight, second_weight, firstMtr, secondMtr
                cost = option_data.trade_cost(d1_bid, d1_ask, first_weight, 0)+option_data.trade_cost\
                    (d2_bid,d2_ask,second_weight,0)+option_data.trade_cost(d1_bid, d1_ask, first_weight, 1)+option_data.trade_cost\
                    (d2_bid,d2_ask,second_weight,1)
                d_cash += straddle_pre.calculate_cash(d1_bid, d1_ask, d2_bid, d2_ask, daily_weight_Q[day_count-1], daily_weight_N[day_count-1], 1)
                d_return = d_cash
                d_cash = straddle_pre.calculate_cash(d1_bid,d1_ask,d2_bid,d2_ask,weight_1,weight_2,0)

        timestamp.append(dailyTradeTime)
        daily_1_maturity.append(Maturity_1)
        daily_2_maturity.append(Maturity_2)
        daily_weight_Q.append(weight_1)
        daily_weight_N.append(weight_2)
        sell_bid_Q_1.append(temp_sell_bid_Q_1)
        sell_bid_Q_2.append(temp_sell_bid_Q_2)
        sell_ask_Q_1.append(temp_sell_ask_Q_1)
        sell_ask_Q_2.append(temp_sell_ask_Q_2)
        sell_bid_N_1.append(temp_sell_bid_N_1)
        sell_bid_N_2.append(temp_sell_bid_N_2)
        sell_ask_N_1.append(temp_sell_ask_N_1)
        sell_ask_N_2.append(temp_sell_ask_N_2)
        buy_bid_Q_1.append(temp_buy_bid_Q_1)
        buy_bid_Q_2.append(temp_buy_bid_Q_2)
        buy_ask_Q_1.append(temp_buy_ask_Q_1)
        buy_ask_Q_2.append(temp_buy_ask_Q_2)
        buy_bid_N_1.append(temp_buy_bid_N_1)
        buy_bid_N_2.append(temp_buy_bid_N_2)
        buy_ask_N_1.append(temp_buy_ask_N_1)
        buy_ask_N_2.append(temp_buy_ask_N_2)
        daily_return.append(d_return)
        cost_list.append(cost)
        net_pos_list.append(new_net_pos)
        cash_balance.append(d_cash)
        cumulative_return.append(sum(daily_return))
        daily_underlying.append(perp_underlying)
        daily_strike.append(ATM_strike)
    day_count += 1

total_data = {'Time': timestamp, 'Underlying': daily_underlying, 'Weight_1': daily_weight_Q, 'Weight_2': daily_weight_N,
              'Strike': daily_strike, 'Maturity_1': daily_1_maturity, 'Maturity_2': daily_2_maturity,
              'Sell_Bid_1_Call': sell_bid_Q_1, 'Sell_Bid_1_Put': sell_bid_Q_2, 'Sell_Ask_1_Call': sell_ask_Q_1,
              'Sell_Ask_1_Put': sell_ask_Q_2, 'Sell_Bid_2_Call': sell_bid_N_1, 'Sell_Bid_2_Put': sell_bid_N_2,
              'Sell_Ask_2_Call': sell_ask_N_1, 'Sell_Ask_2_Put': sell_ask_N_2, 'Buy_Bid_1_Call': buy_bid_Q_1,
              'Buy_Bid_1_Put': buy_bid_Q_2, 'Buy_Ask_1_Call': buy_ask_Q_1, 'Buy_Ask_1_Put': buy_ask_Q_2,
              'Buy_Bid_2_Call': buy_bid_N_1, 'Buy_Bid_2_Put': buy_bid_N_2, 'Buy_Ask_2_Call': buy_ask_N_1,
              'Buy_Ask_2_Put': buy_ask_N_2, 'Daily_Return': daily_return, 'Cummulative_Return': cummulative_return,'Cost':cost_list}
total_df = pd.DataFrame(total_data)
result_dir = project_dir.straddle_result_dir(date=datetime.date.today().strftime("%Y%m%d"))
total_df.to_csv(path_or_buf=result_dir)

plt.plot(timestamp[:-1], cumulative_return[:-1])
plt.show()
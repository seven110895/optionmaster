import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from data_clean import  straddle_prepare
from data_clean import  option_data
from change_directory import directory

project_dir = directory()
option_data = option_data()
tradeHour = datetime.time(16, 0, 0)
delta_T = datetime.time(15,59,0)
dateList = option_data.get_perp_date_list()
startDate = min(dateList)
endDate = max(dateList) + datetime.timedelta(days=1)
option_file_df = option_data.get_option_df()
option_file_by_date = option_file_df.groupby('Date')

daily_1_list, daily_1_weight, daily_2_list, daily_2_weight, daily_strike, daily_time, daily_underlying = [], [], [], [], [], [], []
daily_1_bid, daily_1_ask, daily_2_bid, daily_2_ask, daily_1_maturity, daily_2_maturity = [], [], [], [], [], []
previous_daily_1_list, previous_daily_2_list = [], []
previous_daily_1_bid, previous_daily_1_ask, previous_daily_2_bid, previous_daily_2_ask = [], [], [], []
day_count = 0

for d in np.arange(startDate, endDate):
    dailyTradeTime = datetime.datetime.combine(np.datetime64(d).astype(datetime.date),tradeHour)
    current_day_options = option_file_by_date.get_group(d)
    current_day_options = current_day_options.sort_values(by='Maturity')
    mtr_options = current_day_options.groupby('Maturity')

    straddle_pre = straddle_prepare(current_day_options,tradeHour,d,delta_T)
    if d in dateList:
        #get underlying_price
        perp_underlying = straddle_pre.get_underlying_price(dateList)
        #find one <30 days and one >30 days maturity
        firstMtr,secondMtr = straddle_pre.get_maturity(30)
        if firstMtr ==0 or secondMtr ==0:
            print("False maturity finding method!")
            break
        #linear weight
        first_weight,second_weight = straddle_pre.get_weight(firstMtr,secondMtr)

        #get ATM_strike and ATM options
        ATM_strike = straddle_pre.get_ATM_strike(perp_underlying)
        first_mtr_options = mtr_options.get_group(firstMtr)
        second_mtr_options = mtr_options.get_group(secondMtr)
        first_options = first_mtr_options.groupby('Strike').get_group(ATM_strike)
        first_options = first_options.sort_values(by='CallPut')
        second_options = second_mtr_options.groupby('Strike').get_group(ATM_strike)
        second_options = second_options.sort_values(by='CallPut')

        if len(first_options) != 2 or len(second_options) != 2:
            print("Missing corresponding put/call!")
            break

        #get the bid ask price
        file_1 = first_options['File']
        file_2 = second_options['File']
        d1_bid,d1_ask = straddle_pre.get_bid_ask_price(file_1)
        d2_bid,d2_ask = straddle_pre.get_bid_ask_price(file_2)

        # append daily data to list
        daily_1_maturity.append(firstMtr)
        daily_2_maturity.append(secondMtr)
        daily_1_weight.append(first_weight)
        daily_2_weight.append(second_weight)
        daily_strike.append(ATM_strike)
        daily_underlying.append(perp_underlying)
        daily_1_list.append(file_1)
        daily_2_list.append(file_2)
        daily_1_bid.append(d1_bid)
        daily_1_ask.append(d1_ask)
        daily_2_bid.append(d2_bid)
        daily_2_ask.append(d2_ask)
        daily_time.append(dailyTradeTime)

        #get next day bid ask price
        if day_count == 0:
            p_d_1_list,p_d_2_list = straddle_pre.get_next_day_option(first_options,second_options)
            previous_daily_1_list.append(p_d_1_list)
            previous_daily_2_list.append(p_d_2_list)

        else:
            if day_count == len(dateList)-1:
                p_d_1_list, p_d_2_list = [0,0],[0,0]
            else:
                p_d_1_list, p_d_2_list = straddle_pre.get_next_day_option(first_options, second_options)
            previous_daily_1_list.append(p_d_1_list)
            previous_daily_2_list.append(p_d_2_list)

            pd1_bid,pd1_ask = straddle_pre.get_bid_ask_price(previous_daily_1_list[day_count - 1])
            previous_daily_1_bid.append(pd1_bid)
            previous_daily_1_ask.append(pd1_ask)
            pd2_bid,pd2_ask = straddle_pre.get_bid_ask_price(previous_daily_2_list[day_count - 1])
            previous_daily_2_bid.append(pd2_bid)
            previous_daily_2_ask.append(pd2_ask)
        day_count += 1
previous_daily_1_bid.append([0, 0])
previous_daily_1_ask.append([0, 0])
previous_daily_2_bid.append([0, 0])
previous_daily_2_ask.append([0, 0])

timestamp, daily_weight_Q, daily_weight_N = [], [], []
sell_bid_Q_1, sell_ask_Q_1, sell_bid_N_1, sell_ask_N_1, buy_bid_Q_1, buy_ask_Q_1, buy_bid_N_1, buy_ask_N_1 = [], [], [], [], [], [], [], []
sell_bid_Q_2, sell_ask_Q_2, sell_bid_N_2, sell_ask_N_2, buy_bid_Q_2, buy_ask_Q_2, buy_bid_N_2, buy_ask_N_2 = [], [], [], [], [], [], [], []
daily_return, cummulative_return = [], []

for i in range(0, len(daily_time)):
    timestamp.append(daily_time[i].strftime("%Y/%m/%d-%H:%M:%S.%f"))
    daily_weight_Q.append(daily_1_weight[i])
    daily_weight_N.append(daily_2_weight[i])
    sell_bid_Q_1.append(daily_1_bid[i][0])
    sell_bid_Q_2.append(daily_1_bid[i][1])
    sell_ask_Q_1.append(daily_1_ask[i][0])
    sell_ask_Q_2.append(daily_1_ask[i][1])
    sell_bid_N_1.append(daily_2_bid[i][0])
    sell_bid_N_2.append(daily_2_bid[i][1])
    sell_ask_N_1.append(daily_2_ask[i][0])
    sell_ask_N_2.append(daily_2_ask[i][1])
    buy_bid_Q_1.append(previous_daily_1_bid[i][0])
    buy_bid_Q_2.append(previous_daily_1_bid[i][1])
    buy_ask_Q_1.append(previous_daily_1_ask[i][0])
    buy_ask_Q_2.append(previous_daily_1_ask[i][1])
    buy_bid_N_1.append(previous_daily_2_bid[i][0])
    buy_bid_N_2.append(previous_daily_2_bid[i][1])
    buy_ask_N_1.append(previous_daily_2_ask[i][0])
    buy_ask_N_2.append(previous_daily_2_ask[i][1])


    d_return = option_data.calculate_return((sum(daily_1_bid[i]) + sum(daily_1_ask[i]))/2,(sum(daily_2_bid[i]) + sum(daily_2_ask[i]))/2,
                                            (sum(previous_daily_1_bid[i]) + sum(previous_daily_1_ask[i])) / 2,(sum(previous_daily_2_bid[i]) + sum(previous_daily_2_ask[i]))/2,
                                            daily_1_weight[i],daily_2_weight[i])
    if i == len(daily_time) - 1:
        daily_return.append(0)
        cummulative_return.append(0)
    else:
        daily_return.append(d_return)
        cummulative_return.append(sum(daily_return))

total_data = {'Time': timestamp, 'Underlying': daily_underlying, 'Weight_1': daily_weight_Q, 'Weight_2': daily_weight_N,
              'Strike': daily_strike, 'Maturity_1': daily_1_maturity, 'Maturity_2': daily_2_maturity,
              'Sell_Bid_1_Call': sell_bid_Q_1, 'Sell_Bid_1_Put': sell_bid_Q_2, 'Sell_Ask_1_Call': sell_ask_Q_1,
              'Sell_Ask_1_Put': sell_ask_Q_2, 'Sell_Bid_2_Call': sell_bid_N_1, 'Sell_Bid_2_Put': sell_bid_N_2,
              'Sell_Ask_2_Call': sell_ask_N_1, 'Sell_Ask_2_Put': sell_ask_N_2, 'Buy_Bid_1_Call': buy_bid_Q_1,
              'Buy_Bid_1_Put': buy_bid_Q_2, 'Buy_Ask_1_Call': buy_ask_Q_1, 'Buy_Ask_1_Put': buy_ask_Q_2,
              'Buy_Bid_2_Call': buy_bid_N_1, 'Buy_Bid_2_Put': buy_bid_N_2, 'Buy_Ask_2_Call': buy_ask_N_1,
              'Buy_Ask_2_Put': buy_ask_N_2, 'Daily_Return': daily_return, 'Cummulative_Return': cummulative_return}
total_df = pd.DataFrame(total_data)
result_dir = project_dir.straddle_result_dir(date=datetime.date.today().strftime("%Y%m%d"))
total_df.to_csv(path_or_buf=result_dir)

plt.plot(daily_time[:-1], cummulative_return[:-1])
plt.show()
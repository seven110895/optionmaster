import os
import re
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from change_directory import directory

project_dir = directory()
perpListDir = project_dir.data_download(type='perpetual')
perpList = os.listdir(perpListDir)

dateList = []
for f in perpList:
    f_date = re.split('_', f)
    date = datetime.datetime.strptime(f_date[0], "%Y%m%d").date()
    dateList.append(date)

quarterlyMonth = [3, 6, 9, 12]
monthList = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
startDate = min(dateList)
endDate = max(dateList) + datetime.timedelta(days=1)
tradeHour = datetime.time(16, 0, 0)
optionListDir = project_dir.data_download(type='option')
optionList = os.listdir(optionListDir)

optionDateList, optionMaturityList, optionStrikeList, optionCallPutList, optionMaturityMonthList = [], [], [], [], []
for f in optionList:
    f_date = re.split('_', f)
    date = datetime.datetime.strptime(f_date[0], "%Y%m%d").date()
    optionDateList.append(date)
    mtr = re.split('([A-Z]+)', f_date[1])
    month = monthList.index(mtr[1]) + 1
    maturity = datetime.date(int(mtr[2]) + 2000, month, int(mtr[0]))
    strike = int(f_date[2])
    callPut = re.split('([C,P])', f_date[3])[1]
    optionMaturityList.append(maturity)
    optionMaturityMonthList.append(maturity.month)
    optionStrikeList.append(strike)
    optionCallPutList.append(callPut)
option_file = {'Date': optionDateList, 'Maturity': optionMaturityList, 'MaturityMonth': optionMaturityMonthList,
               'Strike': optionStrikeList, 'CallPut': optionCallPutList, 'File': optionList}
option_file_df = pd.DataFrame(option_file)
option_file_by_date = option_file_df.groupby('Date')

daily_1_list, daily_1_weight, daily_2_list, daily_2_weight, daily_strike, daily_time, daily_underlying = [], [], [], [], [], [], []
daily_1_bid, daily_1_ask, daily_2_bid, daily_2_ask, daily_1_maturity, daily_2_maturity = [], [], [], [], [], []
previous_daily_1_list, previous_daily_2_list = [], []
previous_daily_1_bid, previous_daily_1_ask, previous_daily_2_bid, previous_daily_2_ask = [], [], [], []
day_count = 0

startDate = datetime.date(2019,10,1)
endDate = datetime.date(2020,1,31)
for d in np.arange(startDate, endDate):
    if d in dateList:
        dateIndex = dateList.index(d)
        currentDate = np.datetime64(d).astype(datetime.date)
        perpDir = perpListDir + perpList[dateIndex]
        perpFile = pd.read_csv(filepath_or_buffer=perpDir)
        perpTime = perpFile['Time']
        perpPrice = perpFile['Price']
        perpStartingTime = datetime.datetime.combine(currentDate, datetime.time(0, 0, 0))
        dailyTradeTime = datetime.datetime.combine(currentDate, tradeHour)
        previousTradeTime = dailyTradeTime - datetime.timedelta(minutes=1)
        perp_count = 0
        for t in range(0, len(perpTime)):
            if perpStartingTime + datetime.timedelta(seconds=perpTime[t]) <= dailyTradeTime:
                perp_count = t
            else:
                break
        p_price = perpPrice[perp_count]
        if p_price == 0:
            for t in range(0, perp_count):
                if perpPrice[perp_count - t] != 0:
                    perp_count = perp_count - t
                    break
            p_price = perpPrice[perp_count]
        perp_underlying = p_price

        current_day_options = option_file_by_date.get_group(d)
        current_day_options = current_day_options.sort_values(by='Maturity')
        options_by_mtr_month = current_day_options.groupby('MaturityMonth')
        month_list = []
        for m in options_by_mtr_month.groups:
            month_list.append(m)
        currentMonth = currentDate.month
        if currentMonth not in month_list:
            currentMonth += 1
        if currentMonth > 12:
            currentMonth = currentMonth - 12
        if currentMonth not in month_list:
            print("Wrong month option!")
        current_month_options = options_by_mtr_month.get_group(currentMonth)
        options_by_mtr = current_month_options.groupby('Maturity')
        mtrDates = []
        #近月合约只有一个
        for mtr in options_by_mtr.groups:
            mtrDates.append(mtr)
        if currentDate >= (max(mtrDates) - datetime.timedelta(days=1)):
            currentMonth += 1
            if currentMonth > 12:
                currentMonth = currentMonth - 12
            if currentMonth not in month_list:
                print("Wrong month option!")
                break
            else:
                current_month_options = options_by_mtr_month.get_group(currentMonth)
                options_by_mtr = current_month_options.groupby('Maturity')
                mtrDates = []
                for mtr in options_by_mtr.groups:
                    mtrDates.append(mtr)

        monthMtr = max(mtrDates)

        current_day_options_by_mtr = current_day_options.groupby('Maturity')
        mtrList = []
        for mtr in current_day_options_by_mtr.groups:
            mtrList.append(mtr)
        mtrList = sorted(mtrList)
        secondMtrIndex = len(mtrList) + 1
        for mtr_count in range(0, len(mtrList)):
            if mtrList[mtr_count] - currentDate > datetime.timedelta(days=30):
                secondMtrIndex = mtr_count
                break
        if secondMtrIndex > len(mtrList):
            print("False maturity finding method!")
            break
        else:
            firstMtr = mtrList[secondMtrIndex - 1]
            secondMtr = mtrList[secondMtrIndex]

        # if monthMtr - currentDate > datetime.timedelta(days=31):
        #     # print(mtrDates)
        #     mtrDates.sort()
        #     firstMtr = mtrDates[-2]
        #     secondMtr = monthMtr
        # else:
        #     # secondMonth = -1
        #     if currentMonth == 12:
        #         secondMonth = 3
        #     else:
        #         for m in quarterlyMonth:
        #             if m - currentMonth > 0 and secondMonth == -1:
        #                 secondMonth = m
        #             elif m - currentMonth > 0 and m < secondMonth:
        #                 secondMonth = m
        #     firstMtr = monthMtr
        #     if secondMonth not in month_list:
        #         break
        #     else:
        #         second_month_options = options_by_mtr_month.get_group(secondMonth)
        #         options_by_mtr = second_month_options.groupby('Maturity')
        #         mtrDates = []
        #         for mtr in options_by_mtr.groups:
        #             mtrDates.append(mtr)
        #         secondMtr = max(mtrDates)

        mtr_options = current_day_options.groupby('Maturity')
        first_mtr_options = mtr_options.get_group(firstMtr)
        first_ttm = (datetime.datetime.combine(firstMtr, datetime.time(8, 0, 0)) - dailyTradeTime).total_seconds() / (
                365 * 24 * 60 * 60)
        second_mtr_options = mtr_options.get_group(secondMtr)
        second_ttm = (datetime.datetime.combine(secondMtr, datetime.time(8, 0, 0)) - dailyTradeTime).total_seconds() / (
                365 * 24 * 60 * 60)
        # Linear weight:
        first_weight = ((30 / 365) - second_ttm) / (first_ttm - second_ttm)
        second_weight = 1 - first_weight
        daily_1_maturity.append(firstMtr)
        daily_2_maturity.append(secondMtr)
        daily_1_weight.append(first_weight)
        daily_2_weight.append(second_weight)

        first_mtr_strikes = first_mtr_options['Strike']
        second_mtr_strikes = second_mtr_options['Strike']

        # Option files with certain maturity, strikes ready.
        common_strikes = list(set(first_mtr_strikes).intersection(second_mtr_strikes))
        ATM_strike = common_strikes[0]
        strike_diff = abs(ATM_strike - perp_underlying)
        for x in common_strikes:
            if abs(x - perp_underlying) < strike_diff:
                ATM_strike = x
                strike_diff = abs(x - perp_underlying)
        first_options = first_mtr_options.groupby('Strike').get_group(ATM_strike)
        first_options = first_options.sort_values(by='CallPut')
        second_options = second_mtr_options.groupby('Strike').get_group(ATM_strike)
        second_options = second_options.sort_values(by='CallPut')
        daily_time.append(dailyTradeTime)
        daily_strike.append(ATM_strike)
        daily_underlying.append(perp_underlying)
        if len(first_options) != 2 or len(second_options) != 2:
            print("Missing corresponding put/call!")
            break
        sell_price = 0
        file_1 = first_options['File']
        daily_1_list.append(file_1)
        file_2 = second_options['File']
        daily_2_list.append(file_2)

        d1_bid, d1_ask, d2_bid, d2_ask = [], [], [], []
        for f in file_1:
            data_1_dir = optionListDir + f
            data_1 = pd.read_csv(filepath_or_buffer=data_1_dir)
            data_1_time = data_1['Time']
            data_1_bid = data_1['Bid_1_Price']
            data_1_ask = data_1['Ask_1_Price']
            option_count = 0
            for t_count in range(0, len(data_1_time)):
                t = datetime.datetime.strptime(data_1_time[t_count], "%Y/%m/%d-%H:%M:%S.%f")
                if t_count < 5 and t > (dailyTradeTime - datetime.timedelta(minutes=1)):
                    continue
                if t <= previousTradeTime:
                    option_count = t_count
                else:
                    break
            b_price = data_1_bid[option_count]
            a_price = data_1_ask[option_count]
            if b_price == 0:
                for t_count in range(option_count, len(data_1_time)):
                    if data_1_bid[t_count] != 0:
                        b_price = data_1_bid[t_count]
                        break
            if a_price == 0:
                for t_count in range(option_count, len(data_1_time)):
                    if data_1_ask[t_count] != 0:
                        a_price = data_1_ask[t_count]
                        break
            if b_price == 0 or a_price == 0:
                print('@ ', dailyTradeTime, ': ', f, '>>>Not Available!')
            d1_bid.append(b_price)
            d1_ask.append(a_price)
        daily_1_bid.append(d1_bid)
        daily_1_ask.append(d1_ask)

        for f in file_2:
            data_2_dir = optionListDir + f
            data_2 = pd.read_csv(filepath_or_buffer=data_2_dir)
            data_2_time = data_2['Time']
            data_2_bid = data_2['Bid_1_Price']
            data_2_ask = data_2['Ask_1_Price']
            option_count = 0
            for t_count in range(0, len(data_2_time)):
                t = datetime.datetime.strptime(data_2_time[t_count], "%Y/%m/%d-%H:%M:%S.%f")
                if t_count < 5 and t > (dailyTradeTime - datetime.timedelta(minutes=1)):
                    continue
                if t <= previousTradeTime:
                    option_count = t_count
                else:
                    break
            b_price = data_2_bid[option_count]
            a_price = data_2_ask[option_count]
            if b_price == 0:
                for t_count in range(option_count, len(data_2_time)):
                    if data_2_bid[t_count] != 0:
                        b_price = data_2_bid[t_count]

                        break
            if a_price == 0:
                for t_count in range(option_count, len(data_2_time)):
                    if data_2_ask[t_count] != 0:
                        a_price = data_2_ask[t_count]
                        break
            if b_price == 0 or a_price == 0:
                print('@ ', dailyTradeTime, ': ', f, '>>>Not Available!')
            t = datetime.datetime.strptime(data_2_time[option_count], "%Y/%m/%d-%H:%M:%S.%f")
            d2_bid.append(b_price)
            d2_ask.append(a_price)
        daily_2_bid.append(d2_bid)
        daily_2_ask.append(d2_ask)

        if day_count == 0:
            next_day_count = 1
            nextDate = currentDate + datetime.timedelta(days=next_day_count)
            p_d_1_list, p_d_2_list = [], []
            for row in first_options.iterrows():
                previous_f = re.split('_', row[1]['File'])
                f = nextDate.strftime("%Y%m%d") + '_' + previous_f[1] + '_' + previous_f[2] + '_' + previous_f[3]
                check_exist = optionListDir + f
                while not os.path.isfile(check_exist):
                    next_day_count += 1
                    nextDate = currentDate + datetime.timedelta(days=next_day_count)
                    f = nextDate.strftime("%Y%m%d") + '_' + previous_f[1] + '_' + previous_f[2] + '_' + previous_f[3]
                    check_exist = optionListDir + f
                p_d_1_list.append(f)
            for row in second_options.iterrows():
                previous_f = re.split('_', row[1]['File'])
                f = nextDate.strftime("%Y%m%d") + '_' + previous_f[1] + '_' + previous_f[2] + '_' + previous_f[3]
                p_d_2_list.append(f)
            previous_daily_1_list.append(p_d_1_list)
            previous_daily_2_list.append(p_d_2_list)
            # previous_daily_1_bid.append([0, 0])
            # previous_daily_1_ask.append([0, 0])
            # previous_daily_2_bid.append([0, 0])
            # previous_daily_2_ask.append([0, 0])
        else:
            next_day_count = 1
            nextDate = currentDate + datetime.timedelta(days=next_day_count)
            p_d_1_list, p_d_2_list = [], []
            for row in first_options.iterrows():
                previous_f = re.split('_', row[1]['File'])
                f = nextDate.strftime("%Y%m%d") + '_' + previous_f[1] + '_' + previous_f[2] + '_' + previous_f[3]
                check_exist = optionListDir + f
                while not os.path.isfile(check_exist) and nextDate <= endDate:
                    next_day_count += 1
                    nextDate = currentDate + datetime.timedelta(days=next_day_count)
                    f = nextDate.strftime("%Y%m%d") + '_' + previous_f[1] + '_' + previous_f[2] + '_' + previous_f[3]
                    check_exist = optionListDir + f
                p_d_1_list.append(f)
            for row in second_options.iterrows():
                previous_f = re.split('_', row[1]['File'])
                f = nextDate.strftime("%Y%m%d") + '_' + previous_f[1] + '_' + previous_f[2] + '_' + previous_f[3]
                p_d_2_list.append(f)
            previous_daily_1_list.append(p_d_1_list)
            previous_daily_2_list.append(p_d_2_list)
            pd1_bid, pd1_ask, pd2_bid, pd2_ask = [], [], [], []
            for file in previous_daily_1_list[day_count - 1]:
                p_d_1_dir = optionListDir + file
                p_d_1_data = pd.read_csv(filepath_or_buffer=p_d_1_dir)
                p_d_1_time = p_d_1_data['Time']
                p_d_1_bid = p_d_1_data['Bid_1_Price']
                p_d_1_ask = p_d_1_data['Ask_1_Price']
                p_option_count = 0
                for t_count in range(0, len(p_d_1_time)):
                    t = datetime.datetime.strptime(p_d_1_time[t_count], "%Y/%m/%d-%H:%M:%S.%f")
                    if t_count < 5 and t > (dailyTradeTime - datetime.timedelta(minutes=1)):
                        continue
                    if t <= previousTradeTime:
                        p_option_count = t_count
                    else:
                        break
                pb_price = p_d_1_bid[p_option_count]
                pa_price = p_d_1_ask[p_option_count]
                if pb_price == 0:
                    for t_count in range(p_option_count, len(p_d_1_time)):
                        if p_d_1_bid[t_count] != 0:
                            pb_price = p_d_1_bid[t_count]
                            break
                if pa_price == 0:
                    for t_count in range(p_option_count, len(p_d_1_time)):
                        if p_d_1_ask[t_count] != 0:
                            pa_price = p_d_1_ask[t_count]
                            break
                if pb_price == 0 or pa_price == 0:
                    print('@ ', dailyTradeTime, ': ', file, '>>>Not Available!')
                pd1_bid.append(pb_price)
                pd1_ask.append(pa_price)
            previous_daily_1_bid.append(pd1_bid)
            previous_daily_1_ask.append(pd1_ask)
            for file in previous_daily_2_list[day_count - 1]:
                p_d_2_dir = optionListDir + file
                p_d_2_data = pd.read_csv(filepath_or_buffer=p_d_2_dir)
                p_d_2_time = p_d_2_data['Time']
                p_d_2_bid = p_d_2_data['Bid_1_Price']
                p_d_2_ask = p_d_2_data['Ask_1_Price']
                p_option_count = 0
                for t_count in range(0, len(p_d_2_time)):
                    t = datetime.datetime.strptime(p_d_2_time[t_count], "%Y/%m/%d-%H:%M:%S.%f")
                    if t_count < 5 and t > (dailyTradeTime - datetime.timedelta(minutes=1)):
                        continue
                    if t <= previousTradeTime:
                        p_option_count = t_count
                    else:
                        break
                pb_price = p_d_2_bid[p_option_count]
                pa_price = p_d_2_ask[p_option_count]
                if pb_price == 0:
                    for t_count in range(p_option_count, len(p_d_2_time)):
                        if p_d_2_bid[t_count] != 0:
                            pb_price = p_d_2_bid[t_count]
                            break
                if pa_price == 0:
                    for t_count in range(p_option_count, len(p_d_2_time)):
                        if p_d_2_ask[t_count] != 0:
                            pa_price = p_d_2_ask[t_count]
                            break
                if pb_price == 0 or pa_price == 0:
                    print('@ ', dailyTradeTime, ': ', file, '>>>Not Available!')
                pd2_bid.append(pb_price)
                pd2_ask.append(pa_price)
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
    d_return = daily_1_weight[i] * (sum(daily_1_bid[i]) + sum(daily_1_ask[i]) - sum(previous_daily_1_bid[i]) - sum(
        previous_daily_1_ask[i])) / 2 + daily_2_weight[i] * (
                           sum(daily_2_bid[i]) + sum(daily_2_ask[i]) - sum(previous_daily_2_bid[i]) - sum(
                       previous_daily_2_ask[i])) / 2
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
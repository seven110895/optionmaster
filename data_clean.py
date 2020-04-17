import os
from change_directory import directory
import re
import datetime
import pandas as pd
import numpy as np


class straddle_prepare:
    def __init__(self , current_day_options, tradinghour, d, delta_t, maturity_T):
        self.maturity_T = maturity_T
        self.d = d
        self.tradinghour = tradinghour
        self.currentDate = np.datetime64(d).astype(datetime.date)
        self.current_day_options = current_day_options
        self.project_dir = directory()
        self.dailyTradeTime = datetime.datetime.combine(self.currentDate, self.tradinghour)
        self.delayTradeTime = self.dailyTradeTime + datetime.timedelta(minutes=delta_t)
        self.previousTradeTime = self.dailyTradeTime - datetime.timedelta(minutes=delta_t)

    def get_maturity(self):
        date_distance = self.maturity_T
        current_day_options_by_mtr = self.current_day_options.groupby('Maturity')
        mtr_list = []
        for mtr in current_day_options_by_mtr.groups:
            mtr_list.append(mtr)
        mtr_list = sorted(mtr_list)
        secondMtrIndex = len(mtr_list) + 1
        for mtr_count in range(0, len(mtr_list)):
            if mtr_list[mtr_count] - self.currentDate > datetime.timedelta(days=date_distance):
                secondMtrIndex = mtr_count
                break
        if secondMtrIndex > len(mtr_list):
            firstMtr, secondMtr = 0, 0

        else:
            firstMtr = mtr_list[secondMtrIndex - 1]
            secondMtr = mtr_list[secondMtrIndex]
        return firstMtr, secondMtr

    def get_weight(self, firstMtr, secondMtr):
        first_ttm = (datetime.datetime.combine(firstMtr, datetime.time(8, 0, 0))
                     - self.dailyTradeTime).total_seconds() / (365 * 24 * 60 * 60)

        second_ttm = (datetime.datetime.combine(secondMtr, datetime.time(8, 0, 0))
                      - self.dailyTradeTime).total_seconds() / (365 * 24 * 60 * 60)
        # Linear weight:
        first_weight = ((self.maturity_T / 365) - second_ttm) / (first_ttm - second_ttm)
        second_weight = 1 - first_weight

        return first_weight,second_weight

    def get_ATM_strike(self, firstMtr, secondMtr, perp_underlying):
        mtr_options = self.current_day_options.groupby('Maturity')
        first_mtr_options = mtr_options.get_group(firstMtr)
        second_mtr_options = mtr_options.get_group(secondMtr)

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
        return ATM_strike

    def get_around_ATM_strike(self,strike_list, ATM_strike, around_number):
        max_list = [x for x in strike_list if x >ATM_strike]
        min_list = [x for x in strike_list if x <ATM_strike]
        max_list.sort()
        min_list.sort(reverse=True)
        final_list=max_list[0:around_number]
        final_list.append(ATM_strike)
        final_list.extend(min_list[0:around_number])
        return final_list


    def get_perp_price(self):
        perpListDir = self.project_dir.data_download(type='perpetual')
        perpDir = perpListDir+str(self.d).replace("-", "")+'_PERPETUAL.csv'
        perpFile = pd.read_csv(filepath_or_buffer=perpDir)
        perpTime = perpFile['Time']
        perpPrice = perpFile['Price']
        perpStartingTime = datetime.datetime.combine(self.currentDate, datetime.time(0, 0, 0))
        perp_count = 0
        for t in range(0, len(perpTime)):
            if perpStartingTime + datetime.timedelta(seconds=perpTime[t]) >= self.previousTradeTime:
                perp_count = t
                p_price = perpPrice[perp_count]
                while p_price == 0:
                    perp_count += 1
                    p_price = perpPrice[perp_count]
                break
        perp_underlying = perpPrice[perp_count]
        return perp_underlying

    def change_maturity(self,mtr):
        month_list = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        mtr = re.split('([A-Z]+)', mtr)
        month = month_list.index(mtr[1]) + 1
        maturity = datetime.date(int(mtr[2]) + 2000, month, int(mtr[0]))
        return maturity

    def get_future_price(self):
        future_list_dir = self.project_dir.data_download(type = 'future')
        future_list = os.listdir(future_list_dir)
        current_day_future = []
        current_day_future_mtr = []
        for i in future_list:
            future_list_str = i.split('_')
            if future_list_str[0]  == str(self.d).replace("-", ""):
                current_day_future.append(i)
                mtr = self.change_maturity(future_list_str[1].split('.')[0])
                current_day_future_mtr.append(mtr)
        current_future_price = pd.Series(index= current_day_future_mtr)
        for future_count in range(len(current_day_future)):
            future_file = pd.read_csv(filepath_or_buffer= future_list_dir + current_day_future[future_count])
            future_time = future_file['Time']
            future_price = future_file['Price']
            future_startingtime = datetime.datetime.combine(self.currentDate, datetime.time(0, 0, 0))
            t_count = 0
            for t in range(0,len(future_time)):
                if future_startingtime + datetime.timedelta(seconds=future_time[t]) >= self.previousTradeTime:
                    t_count = t
                    f_price = future_price[t_count]
                    while f_price == 0:
                        t_count += 1
                        f_price = future_price[t_count]
                    break
            current_future_price[current_day_future_mtr[future_count]] = future_price[t_count]
        return current_future_price

    def outer_interpolation(self,mtr1,mtr2,price1,price2,t_mtr):
        t_price = price2 + (price2 - price1) * (t_mtr - mtr2) / (mtr2 - mtr1)
        return t_price

    def calculate_ttm(self,mtr):
        ttm = (datetime.datetime.combine(mtr, datetime.time(8, 0, 0)) - self.dailyTradeTime).total_seconds() / (
                        365 * 24 * 60 * 60)
        return ttm

    def get_bid_ask_price(self, strike, maturity, file):
        # if strike ==0, search by file , else search by strike and maturity.
        d_bid, d_ask = [], []
        if strike != 0 or maturity != 0:
            mtr_options = self.current_day_options.groupby('Maturity')
            first_mtr_options = mtr_options.get_group(maturity)
            first_options = first_mtr_options.groupby('Strike').get_group(strike)
            first_options = first_options.sort_values(by='CallPut')
            file = first_options['File']
        for f in file:
            optionListDir = self.project_dir.data_download(type='option')
            data_1_dir = optionListDir + f
            data_1 = pd.read_csv(filepath_or_buffer=data_1_dir)
            data_1_time = data_1['Time']
            data_1_bid = data_1['Bid_1_Price']
            data_1_ask = data_1['Ask_1_Price']
            option_count = 0
            for t_count in range(0, len(data_1_time)):
                if data_1_time[t_count] == '0':
                    break
                t = datetime.datetime.strptime(data_1_time[t_count], "%Y/%m/%d-%H:%M:%S.%f")
                if t_count < 5 and t > self.delayTradeTime:
                    continue
                if t <= self.previousTradeTime:
                    option_count = t_count
                else:
                    break
            b_price = data_1_bid[option_count]
            a_price = data_1_ask[option_count]

            if b_price == 0:
                for t_count in range(option_count, len(data_1_time)):
                    if data_1_time[t_count] == '0':
                        break
                    t = datetime.datetime.strptime(data_1_time[t_count], "%Y/%m/%d-%H:%M:%S.%f")
                    if data_1_bid[t_count] != 0 and t <= self.delayTradeTime:
                        b_price = data_1_bid[t_count]
                        break
            if a_price == 0:
                for t_count in range(option_count, len(data_1_time)):
                    if data_1_time[t_count] == '0':
                        break
                    t = datetime.datetime.strptime(data_1_time[t_count], "%Y/%m/%d-%H:%M:%S.%f")
                    if data_1_ask[t_count] != 0 and t <= self.delayTradeTime:
                        a_price = data_1_ask[t_count]
                        break
            start_t = datetime.datetime.strptime(data_1_time[option_count], "%Y/%m/%d-%H:%M:%S.%f")
            if option_count == 0 and (start_t < self.previousTradeTime or start_t > self.delayTradeTime):
                b_price = 0
                a_price = 0
            if b_price == 0 or a_price == 0:
                print('@ ', self.delayTradeTime, ': ', f, '>>>Not Available!')
            d_bid.append(b_price)
            d_ask.append(a_price)
        return d_bid,d_ask

    def get_mid_price(self, bid_price, ask_price):
        if bid_price == 0 or ask_price == 0:
            mid_price = 0
        else:
            mid_price = (bid_price+ask_price)/2
        return mid_price

    def get_signal_pos(self, net_pos, new_delta, past_delta, change_contract):
        new_net_pos = net_pos
        signal = "hold"
        if net_pos == 0 and new_delta > 0.1:
            new_net_pos = 1
            signal = "long"
        elif net_pos == 1 and change_contract :
            if past_delta < 0:
                new_net_pos = 0
                signal = 'clean'
                if new_delta > 0.1:
                    new_net_pos = 1
                    signal = 'clean_long'
        elif net_pos == 1 and not change_contract:
            new_net_pos = 0
            signal = 'clean'
            if new_delta > 0.1:
                new_net_pos = 1
                signal = 'clean_long'
        return new_net_pos, signal

    def get_hedge_signal(self, past_delta, change_contract):
        if abs(past_delta) > 0.2 or not change_contract :
            signal = 'clean_short'
        else:
            signal = 'hold'
        return signal

    def calculate_cash(self, daily_1_bid, daily_1_ask, daily_2_bid, daily_2_ask, w1, w2, buy_or_sell):
        # if buy_or_sell=0 means buy
        if buy_or_sell == 0:
            cash = - (w1*(sum(daily_1_bid)+sum(daily_1_ask))/2+w2*(sum(daily_2_bid)+sum(daily_2_ask))/2)
        else:
            cash = (w1 * (sum(daily_1_bid) + sum(daily_1_ask)) / 2 + w2 * (sum(daily_2_bid) + sum(daily_2_ask)) / 2)
        return cash

    def get_all_options_info(self):
        firstMtr, secondMtr = self.get_maturity()
        first_weight, second_weight = self.get_weight(firstMtr, secondMtr)
        ATM_strike = self.get_ATM_strike(firstMtr,secondMtr,self.get_perp_price())
        return [first_weight, second_weight, ATM_strike, firstMtr, secondMtr]



class option_data:
    def __init__(self):
        self.project_dir = directory()

    def get_perp_date_list(self):
        perpListDir = self.project_dir.data_download(type='perpetual')
        perpList = os.listdir(perpListDir)
        dateList = []
        for f in perpList:
            f_date = re.split('_', f)
            date = datetime.datetime.strptime(f_date[0], "%Y%m%d").date()
            dateList.append(date)
        return dateList

    def get_option_df(self):
        month_list = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        option_listdir = self.project_dir.data_download(type='option')
        option_list = os.listdir(option_listdir)

        option_date_list, option_maturity_list, option_strike_list, option_call_put_list, option_maturity_month_list \
            = [], [], [], [], []
        for f in option_list:
            f_date = re.split('_', f)
            date = datetime.datetime.strptime(f_date[0], "%Y%m%d").date()
            option_date_list.append(date)
            mtr = re.split('([A-Z]+)', f_date[1])
            month = month_list.index(mtr[1]) + 1
            maturity = datetime.date(int(mtr[2]) + 2000, month, int(mtr[0]))
            strike = int(f_date[2])
            call_put = re.split('([C,P])', f_date[3])[1]
            option_maturity_list.append(maturity)
            option_maturity_month_list.append(maturity.month)
            option_strike_list.append(strike)
            option_call_put_list.append(call_put)
        option_file = {'Date': option_date_list, 'Maturity': option_maturity_list,
                       'MaturityMonth': option_maturity_month_list, 'Strike': option_strike_list,
                       'CallPut': option_call_put_list, 'File': option_list}
        option_file_df = pd.DataFrame(option_file)
        return option_file_df

    def calculate_return(self, daily1_sell_price, daily2_sell_price, pre_daily1_buy_price, pre_daily2_buy_price, w1, w2):
        daily_return = w1 * (daily1_sell_price-pre_daily1_buy_price)+w2*(daily2_sell_price-pre_daily2_buy_price)
        return daily_return

    def trade_cost(self, bid_price, ask_price, quantity, buy_or_sell):
        # buy_or_sell =0 means buy
        if buy_or_sell == 0:
            cost = (sum(ask_price) - (sum(bid_price)+sum(ask_price))/2)*quantity
        else:
            cost = ((sum(bid_price)+sum(ask_price))/2 - sum(bid_price))*quantity
        return cost



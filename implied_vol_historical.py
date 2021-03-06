import pandas as pd
import numpy as np
import datetime
from change_directory import directory
from data_clean import straddle_prepare
from data_clean import option_data
from get_realtime_data import get_realtime_data
from Black_Scholes import BlackScholes
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from mpl_toolkits.mplot3d import Axes3D

#这里仅计算在当日特定的两个mtr的ATM option

def get_iv(row, bidorask):
    b_s = BlackScholes(row['underlying_price'], interest_rate, dividend, ttm)
    if bidorask == 'bid':
        iv = b_s.BS_impliedVol(row['Strike'], row['m_bid'] * row['underlying_price'], row['CallPut'])
    elif bidorask == 'ask':
        iv = b_s.BS_impliedVol(row['Strike'], row['m_ask'] * row['underlying_price'], row['CallPut'])
    else:
        iv = b_s.BS_impliedVol(row['Strike'], row['m_mid'] * row['underlying_price'], row['CallPut'])
    return iv

def get_delta(row):
    b_s = BlackScholes(row['underlying_price'], interest_rate, dividend, ttm)
    delta = b_s.BS_delta(row['Strike'], row['m_mid_vol'], row['CallPut'])
    return delta

def get_gamma(row):
    b_s = BlackScholes(row['underlying_price'], interest_rate, dividend, ttm)
    gamma = b_s.BS_gamma(row['Strike'], row['m_mid_vol'])
    return gamma

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


project_dir = directory()
option_data = option_data()
tradeHour = datetime.time(16, 0, 0)
delta_T = 1
maturity_T = 7
dateList = option_data.get_perp_date_list()
option_file_df = option_data.get_option_df()
option_file_by_date = option_file_df.groupby('Date')
interest_rate = 0
dividend = 0
day_count = 0
previous_mtr = []
startDate = datetime.date(2019,10,1)
endDate = datetime.date(2020,2,23)
ATM_strike_list = []
for d in np.arange(startDate, endDate):
    if d in dateList:
        dailyTradeTime = datetime.datetime.combine(np.datetime64(d).astype(datetime.date), tradeHour)
        current_day_options = option_file_by_date.get_group(d)
        current_day_options = current_day_options.sort_values(by='Maturity')
        mtr_options = current_day_options.groupby('Maturity')
        Maturity_list = list(set(current_day_options["Maturity"]))
        Maturity_list.sort()
        straddle_pre = straddle_prepare(current_day_options, tradeHour, d, delta_T,maturity_T)
        perp_price = straddle_pre.get_perp_price()
        future_price = straddle_pre.get_future_price()
        ttm_list = [0]
        for i in future_price.index:
            ttm = straddle_pre.calculate_ttm(i)
            ttm_list.append(ttm)
        price_list = [perp_price]
        price_list.extend(future_price.values)
        straddle_mtr1, straddle_mtr2 = straddle_pre.get_maturity()
        if d == (straddle_mtr1 - datetime.timedelta(days = 1)) \
                or ((d.astype(datetime.date).year >= 2020) and (d.astype(datetime.date).month >=2) and (d == (straddle_mtr1 - datetime.timedelta(days = 2)))):
            temp_mtr = Maturity_list[Maturity_list.index(straddle_mtr1)+2]
            mtr_list = list(set([straddle_mtr1, straddle_mtr2] + previous_mtr + [temp_mtr]))
        else:
            mtr_list = list(set([straddle_mtr1, straddle_mtr2] + previous_mtr))

        mtr_count = 0
        for mtr, mtr_group in mtr_options:

            if mtr not in mtr_list:
                continue
            mtr_ttm = straddle_pre.calculate_ttm(mtr)
            if mtr_ttm < max(ttm_list):
                underlying_price = np.interp(mtr_ttm,ttm_list,price_list)
            else:
                underlying_price = straddle_pre.outer_interpolation(ttm_list[-2],ttm_list[-1],price_list[-2],price_list[-1],mtr_ttm)

            mtr_group['underlying_price'] = underlying_price

            # 这里筛选出属于ATM strike 和之前出现过ATM strike的option
            ATM_strike = straddle_pre.get_ATM_strike(straddle_mtr1,straddle_mtr2,underlying_price)
            strike_list = list(set(mtr_group['Strike']))
            around_strike_list = straddle_pre.get_around_ATM_strike(strike_list,ATM_strike,0)
            ATM_strike_list.extend(around_strike_list)
            mtr_group = mtr_group.loc[mtr_group['Strike'].isin(ATM_strike_list),:]
            # 出现不匹配的ATM_strike
            if mtr_group.empty:
                continue

            future_mtr_list = list(future_price.index)
            if len([x for x in future_mtr_list if x > mtr]) > 0 :
                hedge_future_mtr = min([x for x in future_mtr_list if x > mtr])
            else :
                hedge_future_mtr = max(future_mtr_list)

            mtr_group['hedge_future'] = hedge_future_mtr
            mtr_group['hedge_future_price'] = future_price[hedge_future_mtr]

            if mtr == np.datetime64(d).astype(datetime.date):
                continue
            else:
                mtr_group = mtr_group.sort_values(by='Strike')
                file = mtr_group["File"]
                mtr_bid,mtr_ask = straddle_pre.get_bid_ask_price(0, 0, file)
                mtr_group['m_bid'] = mtr_bid
                mtr_group['m_ask'] = mtr_ask
                mtr_group['m_mid'] = mtr_group.apply(lambda row:straddle_pre.get_mid_price(row['m_bid'],row['m_ask']), axis=1)
                ttm = (datetime.datetime.combine(mtr, datetime.time(8, 0, 0)) - dailyTradeTime).total_seconds() / (
                        365 * 24 * 60 * 60)
                mtr_group['m_bid_vol'] = mtr_group.apply(get_iv,bidorask ="bid", axis=1)
                mtr_group['m_ask_vol'] = mtr_group.apply(get_iv,bidorask ="ask", axis=1)
                mtr_group['m_mid_vol'] = mtr_group.apply(get_iv,bidorask ="mid", axis=1)
                mtr_group['m_delta'] = mtr_group.apply(get_delta, axis=1)
                mtr_group['m_gamma'] = mtr_group.apply(get_gamma, axis=1)
                mtr_group['ValueType'] = mtr_group.apply(ValueType_define, axis = 1)
                mtr_group.loc[mtr_group['Strike'] == ATM_strike, 'ValueType'] = 'ATM'
                #mtr_group = mtr_group.replace(-1, np.nan)
                #mtr_group = mtr_group.replace(0, np.nan)

                if mtr_count == 0:
                    daily_mtr_options = mtr_group
                else:
                    daily_mtr_options = daily_mtr_options.append(mtr_group)
                mtr_count += 1

        previous_mtr = mtr_list

        if day_count == 0 :
            all_mtr_options = daily_mtr_options
        else:
            all_mtr_options = all_mtr_options.append(daily_mtr_options)
        day_count += 1

all_mtr_options.to_csv("D:/optionmaster/Straddle/Straddle_vol/All_Vol_7_V5.csv")


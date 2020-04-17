import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from data_clean import straddle_prepare
from data_clean import option_data
from change_directory import directory
from Black_Scholes import BlackScholes

project_dir = directory()
option_data = option_data()
tradeHour = datetime.time(16, 0, 0)
delta_T = 1  # minute
maturity_T = 7
dateList = option_data.get_perp_date_list()
startDate = min(dateList)
endDate = max(dateList) + datetime.timedelta(days=1)
option_file_df = option_data.get_option_df()
option_file_by_date = option_file_df.groupby('Date')
day_count = 0
total_data = pd.DataFrame(columns=('Time', 'Underlying','Today_Underlying_1', 'Today_Underlying_2','Past_Underlying_1','Past_Underlying_2', 'Weight_1', 'Weight_2', 'Strike', 'Maturity_1', 'Maturity_2',
                                   'Bid_1_Call', 'Bid_1_Put', 'Ask_1_Call', 'Ask_1_Put',
                                   'Bid_2_Call', 'Bid_2_Put', 'Ask_2_Call', 'Ask_2_Put', 'Straddle_mtm_pnl',
                                   'cash_balance', 'Straddle_Return', 'Spread_Cost', 'signal', 'gamma', 'Op_delta', 'new_delta', 'past_delta',
                                   'daily_hedge_pos', 'hedge_future_price','hedge_cost', 'cum_hedge_cash', 'hedge_mtm_pnl',
                                   'hedge_pnl','daily_hedge_pnl_usd'))
total_data.loc[0, :] = [0 for _ in range(total_data.shape[1])]

historical_vol = pd.read_csv("D:/optionmaster/Straddle/Straddle_vol/ALL_MTR_STRIKE_V2.csv")

startDate = datetime.date(2019, 10, 1)
endDate = datetime.date(2020, 4, 14)
for d in np.arange(startDate, endDate):
    if d in dateList:
        dailyTradeTime = datetime.datetime.combine(np.datetime64(d).astype(datetime.date), tradeHour)
        current_day_options = option_file_by_date.get_group(d)
        current_day_options = current_day_options.sort_values(by='Maturity')
        mtr_options = current_day_options.groupby('Maturity')
        Maturity_list = list(set(current_day_options["Maturity"]))
        Maturity_list.sort()
        current_day_vol_df = historical_vol.loc[historical_vol['Date'] == str(d), :]
        current_day_vol_df = current_day_vol_df.sort_values(['Maturity', 'CallPut'])

        straddle_pre = straddle_prepare(current_day_options, tradeHour, d, delta_T, maturity_T)
        perp_underlying = straddle_pre.get_perp_price()
        if day_count == 0:
            temp_return = total_data.loc[0, :]
        else:
            temp_return = total_data.loc[day_count - 1, :]

        ## 决定是否调仓的信号，之后具体定义
        option_mtr_weight = straddle_pre.get_all_options_info()
        change_contract = ([temp_return['Maturity_1'], temp_return['Maturity_2']] == [option_mtr_weight[3],
                                                                                      option_mtr_weight[4]])

        # 交易日选取的合约在第二天就要平仓，此时应选的新合约不能再有当天的合约了，因为第二天平不了仓
        if d == (min(option_mtr_weight[3:5]) - datetime.timedelta(days = 1)) or \
                (day_count!=0 and d == (min(temp_return['Maturity_1':'Maturity_2']) - datetime.timedelta(days = 1))):
            change_contract = False
            temp_mtr = Maturity_list[Maturity_list.index(option_mtr_weight[3]) + 2]
            option_mtr_weight[3] = option_mtr_weight[4]
            option_mtr_weight[4] = temp_mtr
            new_first_ttm = (datetime.datetime.combine(option_mtr_weight[3], datetime.time(8, 0, 0))
                                   - dailyTradeTime).total_seconds() / (365 * 24 * 60 * 60)
            new_second_ttm = (datetime.datetime.combine(option_mtr_weight[4], datetime.time(8, 0, 0))
                                   - dailyTradeTime).total_seconds() / (365 * 24 * 60 * 60)
            option_mtr_weight[0] = (new_second_ttm-new_first_ttm) / new_second_ttm
            option_mtr_weight[1] = new_first_ttm/new_second_ttm
            option_mtr_weight[2] = straddle_pre.get_ATM_strike(option_mtr_weight[3],option_mtr_weight[4],perp_underlying)

        ###
        today_vol_df = current_day_vol_df[(current_day_vol_df['Maturity'] == str(option_mtr_weight[3])) | (
                    current_day_vol_df['Maturity'] == str(option_mtr_weight[4]))]
        today_vol_df = today_vol_df[today_vol_df['Strike'] == option_mtr_weight[2]]
        past_vol_df = current_day_vol_df[(current_day_vol_df['Maturity'] == str(temp_return['Maturity_1'])) | (
                    current_day_vol_df['Maturity'] == str(temp_return['Maturity_2']))]
        past_vol_df = past_vol_df[past_vol_df['Strike'] == temp_return['Strike']]
        #current_day_vol_df = pd.merge(today_vol_df, past_vol_df, how='outer')
        ###

        mid_price_list = past_vol_df.loc[:, 'm_mid']
        mid_price_list_today = today_vol_df.loc[:, 'm_mid']
        if day_count == 0:
            miss_price_check = min(mid_price_list_today) > 0
        else :
            miss_price_check = (min(mid_price_list) > 0 and min(mid_price_list_today) > 0)
        past_delta = - (sum(
            past_vol_df.loc[past_vol_df['Maturity'] == str(temp_return['Maturity_1']), 'm_delta']) * \
                     temp_return['Weight_1'] + sum(
            past_vol_df.loc[past_vol_df['Maturity'] == str(temp_return['Maturity_2']), 'm_delta']) * \
                     temp_return['Weight_2'])

        new_delta = - (sum(
            today_vol_df.loc[today_vol_df['Maturity'] == str(option_mtr_weight[3]), 'm_delta']) * \
                    option_mtr_weight[0] + sum(
            today_vol_df.loc[today_vol_df['Maturity'] == str(option_mtr_weight[4]), 'm_delta']) * \
                    option_mtr_weight[1])

        past_gamma =  - (sum(
            past_vol_df.loc[past_vol_df['Maturity'] == str(temp_return['Maturity_1']), 'm_gamma']) * \
                     temp_return['Weight_1'] + sum(
            past_vol_df.loc[past_vol_df['Maturity'] == str(temp_return['Maturity_2']), 'm_gamma']) * \
                     temp_return['Weight_2'])

        new_gamma = - (sum(
            today_vol_df.loc[today_vol_df['Maturity'] == str(option_mtr_weight[3]), 'm_gamma']) * \
                    option_mtr_weight[0] + sum(
            today_vol_df.loc[today_vol_df['Maturity'] == str(option_mtr_weight[4]), 'm_gamma']) * \
                    option_mtr_weight[1])

        past_underlying_1 = np.mean(past_vol_df.loc[past_vol_df['Maturity'] == str(temp_return['Maturity_1']), 'underlying_price'])
        past_underlying_2 = np.mean(past_vol_df.loc[past_vol_df['Maturity'] == str(temp_return['Maturity_2']), 'underlying_price'])
        today_underlying_1 = np.mean(today_vol_df.loc[today_vol_df['Maturity'] == str(option_mtr_weight[3]), 'underlying_price'])
        today_underlying_2 = np.mean(today_vol_df.loc[today_vol_df['Maturity'] == str(option_mtr_weight[4]), 'underlying_price'])
        underlying_list = [today_underlying_1, today_underlying_2, past_underlying_1, past_underlying_2]
        if day_count == 0:
            signal = 'short'
        elif not miss_price_check:
            signal = 'hold'
        else:
            signal = straddle_pre.get_hedge_signal(past_delta, change_contract)

        d1_bid = list(today_vol_df.loc[today_vol_df['Maturity'] == str(option_mtr_weight[3]), 'm_bid'])
        d1_ask = list(today_vol_df.loc[today_vol_df['Maturity'] == str(option_mtr_weight[3]), 'm_ask'])
        d2_bid = list(today_vol_df.loc[today_vol_df['Maturity'] == str(option_mtr_weight[4]), 'm_bid'])
        d2_ask = list(today_vol_df.loc[today_vol_df['Maturity'] == str(option_mtr_weight[4]), 'm_ask'])

        d1_bid_p = list(
            past_vol_df.loc[past_vol_df['Maturity'] == str(temp_return['Maturity_1']), 'm_bid'])
        d1_ask_p = list(
            past_vol_df.loc[past_vol_df['Maturity'] == str(temp_return['Maturity_1']), 'm_ask'])
        d2_bid_p = list(
            past_vol_df.loc[past_vol_df['Maturity'] == str(temp_return['Maturity_2']), 'm_bid'])
        d2_ask_p = list(
            past_vol_df.loc[past_vol_df['Maturity'] == str(temp_return['Maturity_2']), 'm_ask'])

        if signal != "hold":
            weight_mtr_list = [0 for _ in range(5)]
            price_list = [0 for _ in range(8)]
            d_cash, d_return, cost = 0, 0, 0
            mtm_pnl = 0

            if signal == "short":
                price_list = d1_bid + d1_ask + d2_bid + d2_ask
                weight_mtr_list = option_mtr_weight
                cost = option_data.trade_cost(d1_bid, d1_ask, option_mtr_weight[0], 1) \
                       + option_data.trade_cost(d2_bid, d2_ask, option_mtr_weight[1], 1)
                d_cash = straddle_pre.calculate_cash(d1_bid, d1_ask, d2_bid, d2_ask,
                                                     option_mtr_weight[0], option_mtr_weight[1], 1)

                # delta hedge param
                gamma = new_gamma
                Op_delta = new_delta
                hedge_future_price = np.mean(
                    today_vol_df.loc[today_vol_df['Maturity'] == str(option_mtr_weight[4]),
                                           'hedge_future_price'])
                daily_hedge_pos = -Op_delta
                hedge_cost = abs(0.0005 * daily_hedge_pos)  # debited in BTC
                cum_hedge_cash = - hedge_future_price * daily_hedge_pos
                hedge_pnl = 0
                hedge_mtm_pnl = 0
                daily_hedge_pnl_usd = 0

            # clean_long means close the original long position and open a new long position
            elif signal == "clean_short":

                price_list = d1_bid + d1_ask + d2_bid + d2_ask
                weight_mtr_list = option_mtr_weight
                cost = option_data.trade_cost(d1_bid, d1_ask, option_mtr_weight[0], 1) \
                       + option_data.trade_cost(d2_bid, d2_ask, option_mtr_weight[1], 1) \
                       + option_data.trade_cost(d1_bid_p, d1_ask_p, temp_return['Weight_1'], 0) \
                       + option_data.trade_cost(d2_bid_p, d2_ask_p, temp_return['Weight_2'], 0)
                d_return = temp_return['cash_balance'] \
                           + straddle_pre.calculate_cash(d1_bid_p, d1_ask_p, d2_bid_p, d2_ask_p,
                                                         temp_return.loc['Weight_1'], temp_return.loc['Weight_2'], 0)
                d_cash = straddle_pre.calculate_cash(d1_bid, d1_ask, d2_bid, d2_ask,
                                                     option_mtr_weight[0], option_mtr_weight[1], 1)
                #add gamma
                gamma = new_gamma

                # firstly close the old position hedging
                Op_delta = 0
                hedge_future_price = np.mean(past_vol_df.loc[past_vol_df['Maturity'] == str(temp_return['Maturity_2']), 'hedge_future_price'])
                daily_hedge_pos = - (Op_delta - temp_return['Op_delta'])
                hedge_cost = abs(0.0005 * daily_hedge_pos)
                cum_hedge_cash = (- hedge_future_price * daily_hedge_pos) + temp_return['cum_hedge_cash']
                hedge_pnl = cum_hedge_cash / hedge_future_price
                hedge_mtm_pnl = 0
                daily_hedge_pnl_usd = - temp_return['Op_delta'] * (hedge_future_price - temp_return['hedge_future_price'])


                # then open the new position hedging
                Op_delta = new_delta
                daily_hedge_pos = - Op_delta
                hedge_cost += abs(0.0005 * daily_hedge_pos)
                hedge_future_price = np.mean(
                    today_vol_df.loc[today_vol_df['Maturity'] == str(option_mtr_weight[4]), 'hedge_future_price'])
                cum_hedge_cash = - hedge_future_price * daily_hedge_pos

            temp_return = [dailyTradeTime, perp_underlying] + underlying_list + weight_mtr_list + price_list \
                          + [mtm_pnl,d_cash, d_return, cost, signal, gamma] + [Op_delta,new_delta,past_delta, daily_hedge_pos,
                                                                             hedge_future_price, hedge_cost,
                                                                             cum_hedge_cash, hedge_mtm_pnl,hedge_pnl, daily_hedge_pnl_usd]
            total_data.loc[day_count, :] = temp_return
        else:
            if not miss_price_check:
                total_data.loc[day_count, :] = temp_return
                total_data.loc[day_count, 'Straddle_Return':'signal'] = 0, 0, 'miss_trade_price'
                total_data.loc[day_count, 'Straddle_mtm_pnl'] = 0
                total_data.loc[day_count, 'daily_hedge_pos'] = 0
                total_data.loc[day_count, 'hedge_cost'] = 0
                total_data.loc[day_count, 'hedge_mtm_pnl'] = 0
                total_data.loc[day_count, 'hedge_pnl'] = 0
                total_data.loc[day_count, 'daily_hedge_pnl_usd'] = 0
                total_data.loc[day_count, 'Time':'Past_Underlying_2'] = [dailyTradeTime,
                                                                         perp_underlying] + underlying_list
            else :
                #add gamma
                gamma = past_gamma
                Op_delta = past_delta
                daily_hedge_pos = - (Op_delta - temp_return['Op_delta'])
                hedge_future_price = np.mean(
                    past_vol_df.loc[past_vol_df['Maturity'] == str(temp_return['Maturity_2']),
                                           'hedge_future_price'])
                hedge_cost = abs(0.0005 * daily_hedge_pos)
                cum_hedge_cash = (- hedge_future_price * daily_hedge_pos) + temp_return['cum_hedge_cash']

                hedge_mtm_pnl = temp_return['cum_hedge_cash'] / hedge_future_price - temp_return['Op_delta']
                hedge_pnl = 0
                daily_hedge_pnl_usd = - temp_return['Op_delta'] * (hedge_future_price - temp_return['hedge_future_price'])

                total_data.loc[day_count, :] = temp_return
                total_data.loc[day_count, 'Straddle_mtm_pnl'] = straddle_pre.calculate_cash(d1_bid_p, d1_ask_p, d2_bid_p, d2_ask_p,
                                                         temp_return['Weight_1'], temp_return['Weight_2'], 0) + temp_return['cash_balance']
                total_data.loc[day_count, 'Spread_Cost'] = 0
                total_data.loc[day_count, 'Bid_1_Call':'Ask_2_Put'] = d1_bid_p + d1_ask_p + d2_bid_p + d2_ask_p
                total_data.loc[day_count, 'Time':'Past_Underlying_2'] = [dailyTradeTime, perp_underlying] + underlying_list
                total_data.loc[day_count, 'Straddle_Return'] = 0
                total_data.loc[day_count, 'signal':'daily_hedge_pnl_usd'] = [signal,gamma, Op_delta, new_delta, past_delta, daily_hedge_pos,
                                                                               hedge_future_price, hedge_cost,
                                                                               cum_hedge_cash, hedge_mtm_pnl,hedge_pnl,daily_hedge_pnl_usd]
        day_count += 1

total_data['Cum_Straddle_mtm_pnl'] = np.cumsum(total_data['Straddle_Return'])+ total_data['Straddle_mtm_pnl']
total_data['Cum_Spread_cost'] = - np.cumsum(total_data['Spread_Cost'])
total_data['Cum_Straddle_pnl_after_cost'] = total_data['Cum_Straddle_mtm_pnl'] + total_data['Cum_Spread_cost']
total_data['Cum_hedge_mtm_pnl'] = np.cumsum(total_data['hedge_pnl']) + total_data['hedge_mtm_pnl']
total_data['Cum_hedge_cost'] = - np.cumsum(total_data['hedge_cost'])
total_data['Cum_hedge_pnl_after_cost'] = total_data['Cum_hedge_mtm_pnl'] + total_data['Cum_hedge_cost']
total_data['hedge_future_share'] = - total_data['cum_hedge_cash'] / total_data['hedge_future_price']

def BS_max_gamma(underlying,underlying_change,mtr,strike,vol):
    if underlying_change < 0:
        underlying_list = np.arange(underlying + underlying_change, underlying + 1, 1)
    else:
        underlying_list = np.arange(underlying, underlying + underlying_change + 1, 1)
    max_result = 0
    for st in underlying_list:
        b_s = BlackScholes(st, 0, 0, mtr)
        deri = b_s.BS_gamma_deri(strike, vol)
        if abs(deri) > max_result:
            max_result = abs(deri)
    return max_result

def get_option_price_change(date, past_date, strike, Maturity_1, Maturity_2, underlying_change_list):
    result_df = pd.DataFrame(columns= ['File', 'option_price_change', 'implied_vol_change', 'delta', 'gamma', 'vega', 'theta'])
    option_price_1_df = historical_vol[
        (historical_vol['Maturity'] == str(Maturity_1)) & (historical_vol['Strike'] == strike) & (
                    historical_vol['Date'] == str(date))]
    option_price_2_df = historical_vol[
        (historical_vol['Maturity'] == str(Maturity_2)) & (historical_vol['Strike'] == strike) & (
                    historical_vol['Date'] == str(date))]
    past_option_price_1_df = historical_vol[
        (historical_vol['Maturity'] == str(Maturity_1)) & (historical_vol['Strike'] == strike) & (
                    historical_vol['Date'] == str(past_date))]
    past_option_price_2_df = historical_vol[
        (historical_vol['Maturity'] == str(Maturity_2)) & (historical_vol['Strike'] == strike) & (
                    historical_vol['Date'] == str(past_date))]

    option_price_1_df = option_price_1_df.sort_values('CallPut')
    option_price_2_df = option_price_2_df.sort_values('CallPut')
    past_option_price_1_df = past_option_price_1_df.sort_values('CallPut')
    past_option_price_2_df = past_option_price_2_df.sort_values('CallPut')
    new_option_df = option_price_1_df.append(option_price_2_df)
    past_option_df = past_option_price_1_df.append(past_option_price_2_df)
    new_option_df['usd_mid'] = new_option_df['underlying_price'] * new_option_df['m_mid']
    past_option_df['usd_mid'] = past_option_df['underlying_price'] * past_option_df['m_mid']
    result_df['option_price_change'] = np.array(new_option_df['usd_mid']) - np.array(past_option_df['usd_mid'])
    result_df['implied_vol_change'] = np.array(new_option_df['m_mid_vol']) - np.array(past_option_df['m_mid_vol'])
    result_df['delta'] = list(past_option_df['m_delta'])
    result_df['gamma'] = list(past_option_df['m_gamma'])
    result_df['vega'] = list(past_option_df['vega'])
    result_df['theta'] = list(past_option_df['theta'])
    max_gamma_list = []
    for count in range(past_option_df.shape[0]):
        underlying = past_option_df.iloc[count, 8]
        underlying_change = underlying_change_list[count]
        mtr = past_option_df.iloc[count, -4]
        vol = past_option_df.iloc[count, 16]
        max_gamma = BS_max_gamma(underlying,underlying_change,mtr,strike,vol)
        max_gamma_list.append(max_gamma)
    result_df['max_gamma_deri'] = max_gamma_list
    result_df['File'] = list(past_option_df['File'])
    return result_df

def get_pnl_attribution(underlying_price_change, dt, d_sigma, delta, theta, gamma, vega, max_gamma_deri):
    delta_pnl = delta * underlying_price_change
    gamma_pnl = 0.5 * gamma * (underlying_price_change ** 2)
    theta_pnl = theta * dt
    vega_pnl = vega * d_sigma
    taylor_error = abs(1/6 * max_gamma_deri * (underlying_price_change ** 3))
    return [delta_pnl, gamma_pnl, theta_pnl, vega_pnl, taylor_error]

total_data['Weight_1'] = -total_data['Weight_1']
total_data['Weight_2'] = -total_data['Weight_2']
total_data['straddle_mtm_return_usd'], total_data['delta_pnl'],\
total_data['gamma_pnl'],total_data['theta_pnl'], total_data['vega_pnl'], total_data['taylor_error'] = np.nan, np.nan, np.nan, np.nan, np.nan, np.nan


# pnl attribution
for i in range(len(total_data)):
    if i == 0:
        pass
    else:
        if total_data.loc[i, 'signal'] != 'miss_trade_price':
            if total_data.loc[i-1, 'signal'] == 'miss_trade_price':
                past_num = i - 2
            else:
                past_num = i - 1
            underlying_change_1 = total_data.loc[i, 'Past_Underlying_1'] - total_data.loc[past_num, 'Today_Underlying_1']
            underlying_change_2 = total_data.loc[i, 'Past_Underlying_2'] - total_data.loc[past_num, 'Today_Underlying_2']
            underlying_change_list = [underlying_change_1,underlying_change_1,underlying_change_2,underlying_change_2]
            weight_list = [total_data.loc[past_num, 'Weight_1'],total_data.loc[past_num, 'Weight_1'],total_data.loc[past_num, 'Weight_2'],total_data.loc[past_num, 'Weight_2']]
            delta_pnl, gamma_pnl, vega_pnl, theta_pnl, taylor_error = 0, 0, 0, 0, 0
            temp_df = get_option_price_change(total_data.loc[i, 'Time'].date(), total_data.loc[past_num, 'Time'].date(),
                                              total_data.loc[past_num, 'Strike'], total_data.loc[past_num, 'Maturity_1'],
                                              total_data.loc[past_num, 'Maturity_2'], underlying_change_list)
            straddle_mtm_return_usd = sum(np.array(temp_df['option_price_change']) * np.array(weight_list))

            dt = (total_data.loc[i, 'Time'] - total_data.loc[past_num, 'Time']).total_seconds() / (365 * 24 * 60 * 60)
            for num in range(4):

                greek_pnl_list = get_pnl_attribution(underlying_change_list[num], dt,
                                                     temp_df.loc[num, 'implied_vol_change'], temp_df.loc[num, 'delta'],
                                                     temp_df.loc[num, 'theta'], temp_df.loc[num, 'gamma'],
                                                     temp_df.loc[num, 'vega'], temp_df.loc[num, 'max_gamma_deri'])
                delta_pnl += greek_pnl_list[0] * weight_list[num]
                gamma_pnl += greek_pnl_list[1] * weight_list[num]
                theta_pnl += greek_pnl_list[2] * weight_list[num]
                vega_pnl += greek_pnl_list[3] * weight_list[num]
                taylor_error += greek_pnl_list[4] * weight_list[num]
            total_data.loc[
                i, ['straddle_mtm_return_usd', 'delta_pnl', 'gamma_pnl', 'theta_pnl', 'vega_pnl', 'taylor_error']] = [
                straddle_mtm_return_usd, delta_pnl, gamma_pnl, theta_pnl, vega_pnl, taylor_error]
        else:
            pass
total_data['taylor_error'] = abs(total_data['taylor_error'])
total_data['hedge_error'] = total_data['straddle_mtm_return_usd'] - total_data['delta_pnl'] - total_data['gamma_pnl'] - total_data['theta_pnl'] - total_data['vega_pnl']
total_data['hedge_error_after_taylor'] = total_data.apply(lambda row: row['hedge_error'] - row['taylor_error'] if row['hedge_error'] > 0 else row['hedge_error'] + row['taylor_error'],axis = 1 )
total_data['hedge_error_pct'] = total_data['hedge_error_after_taylor'] / total_data['straddle_mtm_return_usd']

total_data_df = total_data.loc[:, ['Time', 'Underlying', 'Weight_1', 'Weight_2', 'Strike', 'Maturity_1', 'Maturity_2',
                                   'Bid_1_Call', 'Bid_1_Put', 'Ask_1_Call', 'Ask_1_Put',
                                   'Bid_2_Call', 'Bid_2_Put', 'Ask_2_Call', 'Ask_2_Put', 'signal', 'gamma','Op_delta',
                                   'new_delta','past_delta', 'daily_hedge_pos', 'hedge_future_share',
                                   'Cum_Straddle_mtm_pnl', 'Cum_Spread_cost', 'Cum_Straddle_pnl_after_cost',
                                   'Cum_hedge_mtm_pnl', 'Cum_hedge_cost', 'Cum_hedge_pnl_after_cost',
                                   'straddle_mtm_return_usd', 'delta_pnl', 'daily_hedge_pnl_usd','gamma_pnl', 'theta_pnl', 'vega_pnl',
                                   'taylor_error', 'hedge_error', 'hedge_error_after_taylor', 'hedge_error_pct']]
for pct in ['delta_pnl', 'gamma_pnl', 'theta_pnl', 'vega_pnl', 'taylor_error']:
    total_data_df[pct + '_pct'] = total_data_df[pct] / total_data_df['straddle_mtm_return_usd']
total_data_df.to_csv("D:/optionmaster/Straddle/Straddle_vol/Straddle_20200415_date_distance_14_V6.csv")
total_data.to_csv("D:/optionmaster/Straddle/Straddle_vol/Straddle_pnl_decom.csv")
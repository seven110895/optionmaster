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
delta_T = 1  # minute
maturity_T = 7
dateList = option_data.get_perp_date_list()
startDate = min(dateList)
endDate = max(dateList) + datetime.timedelta(days=1)
option_file_df = option_data.get_option_df()
option_file_by_date = option_file_df.groupby('Date')
day_count = 0
total_data = pd.DataFrame(columns=('Time', 'Underlying', 'Weight_1', 'Weight_2', 'Strike', 'Maturity_1', 'Maturity_2',
                                   'Bid_1_Call', 'Bid_1_Put', 'Ask_1_Call', 'Ask_1_Put',
                                   'Bid_2_Call', 'Bid_2_Put', 'Ask_2_Call', 'Ask_2_Put', 'Straddle_mtm_pnl',
                                   'cash_balance', 'Straddle_Return', 'Spread_Cost', 'signal', 'gamma', 'Op_delta', 'new_delta', 'past_delta',
                                   'daily_hedge_pos', 'hedge_future_price', 'hedge_cost', 'cum_hedge_cash', 'hedge_mtm_pnl',
                                   'hedge_pnl'))
total_data.loc[0, :] = [0 for _ in range(total_data.shape[1])]

historical_vol = pd.read_csv("D:/optionmaster/Straddle/Straddle_vol/All_Vol_" + str(maturity_T) + "_V5.csv")

startDate = datetime.date(2019, 10, 1)
endDate = datetime.date(2020, 2, 23)
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
                hedge_future_price = np.mean(past_vol_df.loc[past_vol_df['Maturity'] == str(temp_return['Maturity_2']),'hedge_future_price'])
                daily_hedge_pos = - (Op_delta - temp_return['Op_delta'])
                hedge_cost = abs(0.0005 * daily_hedge_pos)
                cum_hedge_cash = (- hedge_future_price * daily_hedge_pos) + temp_return['cum_hedge_cash']
                hedge_pnl = cum_hedge_cash / hedge_future_price
                hedge_mtm_pnl = 0
                # then open the new position hedging
                Op_delta = new_delta
                daily_hedge_pos = - Op_delta
                hedge_cost += abs(0.0005 * daily_hedge_pos)
                hedge_future_price = np.mean(
                    today_vol_df.loc[today_vol_df['Maturity'] == str(option_mtr_weight[4]), 'hedge_future_price'])
                cum_hedge_cash = - hedge_future_price * daily_hedge_pos

            temp_return = [dailyTradeTime, perp_underlying] + weight_mtr_list + price_list \
                          + [mtm_pnl,d_cash, d_return, cost, signal, gamma] + [Op_delta,new_delta,past_delta, daily_hedge_pos,
                                                                             hedge_future_price, hedge_cost,
                                                                             cum_hedge_cash, hedge_mtm_pnl,hedge_pnl]
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
                total_data.loc[day_count, 'Time':'Underlying'] = [dailyTradeTime, perp_underlying]
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

                hedge_mtm_pnl = temp_return['cum_hedge_cash']/ hedge_future_price - temp_return['Op_delta']
                hedge_pnl = 0
                total_data.loc[day_count, :] = temp_return
                total_data.loc[day_count, 'Straddle_mtm_pnl'] = straddle_pre.calculate_cash(d1_bid_p, d1_ask_p, d2_bid_p, d2_ask_p,
                                                         temp_return['Weight_1'], temp_return['Weight_2'], 0) + temp_return['cash_balance']
                total_data.loc[day_count, 'Spread_Cost'] = 0
                total_data.loc[day_count, 'Bid_1_Call':'Ask_2_Put'] = d1_bid_p + d1_ask_p + d2_bid_p + d2_ask_p
                total_data.loc[day_count, 'Time':'Underlying'] = [dailyTradeTime, perp_underlying]
                total_data.loc[day_count, 'Straddle_Return'] = 0
                total_data.loc[day_count, 'signal':'hedge_pnl'] = [signal,gamma, Op_delta, new_delta, past_delta, daily_hedge_pos,
                                                                               hedge_future_price, hedge_cost,
                                                                               cum_hedge_cash, hedge_mtm_pnl,hedge_pnl]
        day_count += 1

total_data['Cum_Straddle_mtm_pnl'] = np.cumsum(total_data['Straddle_Return'])+ total_data['Straddle_mtm_pnl']
total_data['Cum_Spread_cost'] = - np.cumsum(total_data['Spread_Cost'])
total_data['Cum_Straddle_pnl_after_cost'] = total_data['Cum_Straddle_mtm_pnl'] + total_data['Cum_Spread_cost']
total_data['Cum_hedge_mtm_pnl'] = np.cumsum(total_data['hedge_pnl']) + total_data['hedge_mtm_pnl']
total_data['Cum_hedge_cost'] = - np.cumsum(total_data['hedge_cost'])
total_data['Cum_hedge_pnl_after_cost'] = total_data['Cum_hedge_mtm_pnl'] + total_data['Cum_hedge_cost']
total_data['hedge_future_share'] = - total_data['cum_hedge_cash'] / total_data['hedge_future_price']

total_data_df = total_data.loc[:, ['Time', 'Underlying', 'Weight_1', 'Weight_2', 'Strike', 'Maturity_1', 'Maturity_2',
                                   'Bid_1_Call', 'Bid_1_Put', 'Ask_1_Call', 'Ask_1_Put',
                                   'Bid_2_Call', 'Bid_2_Put', 'Ask_2_Call', 'Ask_2_Put', 'signal', 'gamma','Op_delta','new_delta','past_delta', 'daily_hedge_pos', 'hedge_future_share',
                                   'Cum_Straddle_mtm_pnl', 'Cum_Spread_cost', 'Cum_Straddle_pnl_after_cost',
                                   'Cum_hedge_mtm_pnl', 'Cum_hedge_cost', 'Cum_hedge_pnl_after_cost']]
total_data_df['Weight_1'] = -total_data_df['Weight_1']
total_data_df['Weight_2'] = -total_data_df['Weight_2']



#total_data['hedge_pnl'] = np.cumsum(total_data['realized_hedge_return'] - total_data['hedge_cost'])
total_data_df.to_csv("D:/optionmaster/Straddle/Straddle_vol/Straddle_20200303_date_distance" + str(maturity_T) + '_V5.csv')

#plt.plot(total_data['Time'], total_data['cumulative_return'])
#plt.show()
writer = pd.ExcelWriter("D:/optionmaster/Straddle/Straddle_vol/Straddle_20200304_all_date_distance_V6.xlsx")
for dis in [7,14,30] :
    dis_df = pd.read_csv("D:/optionmaster/Straddle/Straddle_vol/Straddle_20200303_date_distance" + str(dis) + '_V5.csv')
    dis_df.to_excel(writer, sheet_name='date_distance_'+str(dis), index=False)
writer.save()

dis_df_7 = pd.read_csv("D:/optionmaster/Straddle/Straddle_vol/Straddle_20200303_date_distance" + str(7) + '_V5.csv')
dis_df_14 = pd.read_csv("D:/optionmaster/Straddle/Straddle_vol/Straddle_20200303_date_distance" + str(14) + '_V5.csv')
dis_df_30 = pd.read_csv("D:/optionmaster/Straddle/Straddle_vol/Straddle_20200303_date_distance" + str(30) + '_V5.csv')

clean_list = []
for df in [dis_df_7, dis_df_14, dis_df_30] :
    temp_len = df.loc[df['signal'] == 'clean_short',:].shape[0]
    clean_list.append(temp_len)

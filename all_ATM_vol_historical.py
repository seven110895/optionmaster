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


# 这里的脚本是导出所有mtr的ATM_vol , 并绘制ATM-vol term structure

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


def get_gamma(row):
    b_s = BlackScholes(row['underlying_price'], interest_rate, dividend, ttm)
    gamma = b_s.BS_gamma(row['Strike'], row['m_mid_vol'])
    return gamma


project_dir = directory()
option_data = option_data()
tradeHour = datetime.time(16, 0, 0)
delta_T = 1
dateList = option_data.get_perp_date_list()
option_file_df = option_data.get_option_df()
option_file_by_date = option_file_df.groupby('Date')
interest_rate = 0
dividend = 0
day_count = 0
previous_mtr = []
startDate = datetime.date(2019, 10, 4)
endDate = datetime.date(2019, 11, 4)

for d in np.arange(startDate, endDate):
    if d in dateList:
        dailyTradeTime = datetime.datetime.combine(np.datetime64(d).astype(datetime.date), tradeHour)
        current_day_options = option_file_by_date.get_group(d)
        current_day_options = current_day_options.sort_values(by='Maturity')
        mtr_options = current_day_options.groupby('Maturity')
        Maturity_list = set(current_day_options["Maturity"])
        straddle_pre = straddle_prepare(current_day_options, tradeHour, d, delta_T)
        perp_price = straddle_pre.get_perp_price()
        future_price = straddle_pre.get_future_price()
        ttm_list = [0]
        for i in future_price.index:
            ttm = straddle_pre.calculate_ttm(i)
            ttm_list.append(ttm)
        price_list = [perp_price]
        price_list.extend(future_price.values)

        mtr_count = 0
        for mtr, mtr_group in mtr_options:

            mtr_ttm = straddle_pre.calculate_ttm(mtr)
            if mtr_ttm < max(ttm_list):
                underlying_price = np.interp(mtr_ttm, ttm_list, price_list)
            else:
                underlying_price = straddle_pre.outer_interpolation(ttm_list[-2], ttm_list[-1], price_list[-2],
                                                                    price_list[-1], mtr_ttm)

            mtr_group['underlying_price'] = underlying_price
            # ATM_strike = straddle_pre.get_ATM_strike(underlying_price)
            # strike_list = list(set(mtr_group['Strike']))
            # around_strike_list = straddle_pre.get_around_ATM_strike(strike_list,ATM_strike,0)
            # mtr_group = mtr_group.loc[mtr_group['Strike'].isin(around_strike_list),:]

            # future_mtr_list = list(future_price.index)
            # hedge_future_mtr = min([x for x in future_mtr_list if x > mtr])
            # mtr_group['hedge_future'] = hedge_future_mtr
            # mtr_group['hedge_future_price'] = future_price[hedge_future_mtr]

            if mtr == np.datetime64(d).astype(datetime.date):
                continue
            else:
                mtr_group = mtr_group.sort_values(by='Strike')
                file = mtr_group["File"]
                mtr_bid, mtr_ask = straddle_pre.get_bid_ask_price(0, 0, file)
                mtr_group['m_bid'] = mtr_bid
                mtr_group['m_ask'] = mtr_ask
                mtr_group['m_mid'] = mtr_group.apply(lambda row: straddle_pre.get_mid_price(row['m_bid'], row['m_ask']),
                                                     axis=1)
                ttm = (datetime.datetime.combine(mtr, datetime.time(8, 0, 0)) - dailyTradeTime).total_seconds() / (
                        365 * 24 * 60 * 60)
                mtr_group['m_bid_vol'] = mtr_group.apply(get_iv, bidorask="bid", axis=1)
                mtr_group['m_ask_vol'] = mtr_group.apply(get_iv, bidorask="ask", axis=1)
                mtr_group['m_mid_vol'] = mtr_group.apply(get_iv, bidorask="mid", axis=1)
                mtr_group['m_delta'] = mtr_group.apply(get_delta, axis=1)
                mtr_group['ValueType'] = mtr_group.apply(ValueType_define, axis=1)
                # mtr_group.loc[mtr_group['Strike'] == ATM_strike, 'ValueType'] = 'ATM'
                # mtr_group = mtr_group.replace(-1, np.nan)
                # mtr_group = mtr_group.replace(0, np.nan)

                if mtr_count == 0:
                    daily_mtr_options = mtr_group
                else:
                    daily_mtr_options = daily_mtr_options.append(mtr_group)
                mtr_count += 1

        if day_count == 0:
            all_mtr_options = daily_mtr_options
        else:
            all_mtr_options = all_mtr_options.append(daily_mtr_options)
        day_count += 1

# all_mtr_options.to_csv("/Users/wenjinfeng/Downloads/OptionResearch-master/Straddle/vol_history/Oct_all.csv")
all_mtr_options = pd.read_csv("D:/optionmaster/Straddle/Straddle_vol/Oct_all.csv")
all_mtr_options = all_mtr_options.replace(-1, np.nan)

pdf = PdfPages("D:/optionmaster/Straddle/Vol_plot/ATM_vol_term_structure.pdf")
vol_df_mtr = all_mtr_options.groupby('Maturity')
mtr_count = 0
for mtr, mtr_group in vol_df_mtr:
    mtr_group_by_day = mtr_group.groupby('Date')
    day_count = 0
    for day, daily_mtr_group in mtr_group_by_day:
        spread_list = list(abs(daily_mtr_group['Strike'] - daily_mtr_group['underlying_price']))
        index = spread_list.index(min(spread_list))
        ATM_strike = list(daily_mtr_group['Strike'])[index]

        if day_count == 0:
            ATM_Vol_df = daily_mtr_group.loc[daily_mtr_group['Strike'] == ATM_strike, :]
        else:
            ATM_Vol_df = ATM_Vol_df.append(daily_mtr_group.loc[daily_mtr_group['Strike'] == ATM_strike, :])
        day_count += 1

    ATM_Call_df = ATM_Vol_df.loc[ATM_Vol_df['CallPut'] == 'C', :]
    ATM_Put_df = ATM_Vol_df.loc[ATM_Vol_df['CallPut'] == 'P', :]

    if mtr_count == 0:
        all_ATM_Call_df = ATM_Call_df
        all_ATM_Put_df = ATM_Put_df
        all_ATM_df = ATM_Vol_df
    else:
        all_ATM_Call_df = all_ATM_Call_df.append(ATM_Call_df)
        all_ATM_Put_df = all_ATM_Put_df.append(ATM_Put_df)
        all_ATM_df = all_ATM_df.append(ATM_Vol_df)
    mtr_count += 1
    plt.figure(figsize=(6, 6))
    fig = plt.figure(1)
    ax1 = plt.subplot(211)
    ax1.plot(ATM_Call_df['Date'], ATM_Call_df['m_bid_vol'], '.-')
    ax1.plot(ATM_Call_df['Date'], ATM_Call_df['m_ask_vol'], '.-')
    ax1.plot(ATM_Call_df['Date'], ATM_Call_df['m_mid_vol'], '.-')
    ax1.legend(loc='upper right')
    ax1.set_title('Maturity:' + str(mtr) + ' Call Vol Term Structure')

    ax2 = plt.subplot(212)
    ax2.plot(ATM_Put_df['Date'], ATM_Put_df['m_bid_vol'], '.-')
    ax2.plot(ATM_Put_df['Date'], ATM_Put_df['m_ask_vol'], '.-')
    ax2.plot(ATM_Put_df['Date'], ATM_Put_df['m_mid_vol'], '.-')
    ax2.legend(loc='upper right')
    ax2.set_title('Maturity:' + str(mtr) + ' Put Vol Term Structure')

    plt.tight_layout()
    pdf.savefig()
    plt.close()
pdf.close()

mtr_count = 0
pdf = PdfPages("D:/optionmaster/Straddle/Vol_plot/ATM_vol_term_structure_V2.pdf")
vol_df_mtr = all_mtr_options.groupby('Date')
for mtr, mtr_group in vol_df_mtr:
    mtr_group_by_day = mtr_group.groupby('Maturity')
    day_count = 0
    for day, daily_mtr_group in mtr_group_by_day:
        spread_list = list(abs(daily_mtr_group['Strike'] - daily_mtr_group['underlying_price']))
        index = spread_list.index(min(spread_list))
        ATM_strike = list(daily_mtr_group['Strike'])[index]

        if day_count == 0:
            ATM_Vol_df = daily_mtr_group.loc[daily_mtr_group['Strike'] == ATM_strike, :]
        else:
            ATM_Vol_df = ATM_Vol_df.append(daily_mtr_group.loc[daily_mtr_group['Strike'] == ATM_strike, :])
        day_count += 1
    ATM_Call_df = ATM_Vol_df.loc[ATM_Vol_df['CallPut'] == 'C', :]
    ATM_Put_df = ATM_Vol_df.loc[ATM_Vol_df['CallPut'] == 'P', :]

    if mtr_count == 0:
        all_ATM_Call_df = ATM_Call_df
        all_ATM_Put_df = ATM_Put_df
        all_ATM_df = ATM_Vol_df
    else:
        all_ATM_Call_df = all_ATM_Call_df.append(ATM_Call_df)
        all_ATM_Put_df = all_ATM_Put_df.append(ATM_Put_df)
        all_ATM_df = all_ATM_df.append(ATM_Vol_df)
    mtr_count += 1

    plt.figure(figsize=(6, 6))
    fig = plt.figure(1)
    ax1 = plt.subplot(211)
    ax1.plot(ATM_Call_df['Maturity'], ATM_Call_df['m_bid_vol'], '.-', label='bid_vol')
    ax1.plot(ATM_Call_df['Maturity'], ATM_Call_df['m_ask_vol'], '.-', label='ask_vol')
    ax1.plot(ATM_Call_df['Maturity'], ATM_Call_df['m_mid_vol'], '.-', label='mid_vol')
    ax1.legend(loc='best')
    ax1.set_ylim((0.4, 1))
    ax1.set_title(str(mtr) + ' ATM Call Vol Term Structure')

    ax2 = plt.subplot(212)
    ax2.plot(ATM_Put_df['Maturity'], ATM_Put_df['m_bid_vol'], '.-', label='bid_vol')
    ax2.plot(ATM_Put_df['Maturity'], ATM_Put_df['m_ask_vol'], '.-', label='ask_vol')
    ax2.plot(ATM_Put_df['Maturity'], ATM_Put_df['m_mid_vol'], '.-', label='mid_vol')
    ax2.legend(loc='best')
    ax2.set_ylim((0.4, 1))
    ax2.set_title(str(mtr) + ' ATM Put Vol Term Structure')

    plt.tight_layout()
    pdf.savefig()
    plt.close()
pdf.close()

all_ATM_df['ValueType'] = 'ATM'
all_ATM_df = all_ATM_df.iloc[:, 1::]
all_ATM_df.to_csv("D:/optionmaster/Straddle/Vol_plot/ATM_vol_term_structure.csv")
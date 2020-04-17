import pandas as pd
import numpy as np
import datetime
from change_directory import directory
from data_clean import straddle_prepare
from data_clean import option_data
from get_realtime_data import get_realtime_data
from Black_Scholes import BlackScholes
from data_transform import data_transform
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from mpl_toolkits.mplot3d import Axes3D


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
        if row['Strike'] < row['underlying_price_x']:
            money_type = 'ITM'
        elif row['Strike'] > row['underlying_price_x']:
            money_type = 'OTM'
        else:
            money_type = 'ATM'
    else:
        if row['Strike'] < row['underlying_price_x']:
            money_type = 'OTM'
        elif row['Strike'] > row['underlying_price_x']:
            money_type = 'ITM'
        else:
            money_type = 'ATM'
    return money_type

startDate = datetime.date.today() - datetime.timedelta(days = 1)
endDate = datetime.date.today()
data_transform(startDate, endDate)
project_dir = directory()
option_data = option_data()
tradeHour = datetime.time(16, 0, 0)
delta_T = 1
maturity_T = 30
dateList = option_data.get_perp_date_list()
option_file_df = option_data.get_option_df()
option_file_by_date = option_file_df.groupby('Date')
interest_rate = 0
dividend = 0
day_count = 0


realtime_dir = get_realtime_data()
realtime_all_mtr_options = realtime_dir.get_tradetime_vol( datetime.datetime.combine(np.datetime64(startDate).astype(datetime.date), tradeHour), 1)
#realtime_orderbook_dir = project_dir.realtime_orderbook_dir(startDate)
#realtime_all_mtr_options.to_csv(realtime_orderbook_dir)
#realtime_all = pd.read_csv(realtime_orderbook_dir)
#realtime_all_mtr_options= realtime_all.iloc[: ,1:]
#realtime_all_mtr_options = realtime_all_mtr_options.replace(0,np.nan)

realtime_all_mtr_options['bid_iv'] = realtime_all_mtr_options['bid_iv'] /100
realtime_all_mtr_options['ask_iv'] = realtime_all_mtr_options['ask_iv'] /100
realtime_all_mtr_options['mark_iv'] = realtime_all_mtr_options['mark_iv'] /100


for d in np.arange(startDate, endDate):
    dailyTradeTime = datetime.datetime.combine(np.datetime64(d).astype(datetime.date), tradeHour)
    current_day_options = option_file_by_date.get_group(d)
    current_day_options = current_day_options.sort_values(by='Maturity')
    mtr_options = current_day_options.groupby('Maturity')
    Maturity_list = set(current_day_options["Maturity"])
    straddle_pre = straddle_prepare(current_day_options, tradeHour, d, delta_T, maturity_T)
    if d in dateList:
        mtr_count = 0
        for mtr, mtr_group in mtr_options:
            mtr_group = pd.merge(mtr_group, realtime_all_mtr_options.loc[:, ['Maturity', 'Strike', 'CallPut',
                                                                             'underlying_price']],
                                 how='left', on=['Maturity', 'Strike', 'CallPut'])
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
                #mtr_group = mtr_group.replace(-1, np.nan)
                #mtr_group = mtr_group.replace(0, np.nan)

                if mtr_count == 0:
                    daily_mtr_options = mtr_group
                else:
                    daily_mtr_options = daily_mtr_options.append(mtr_group)
                mtr_count += 1

        if day_count == 0 :
            all_mtr_options = daily_mtr_options
        else:
            all_mtr_options = all_mtr_options.append(daily_mtr_options)
        day_count += 1

result_dir = project_dir.implied_vol_compare_dir(date=datetime.date.today().strftime("%Y%m%d"))
writer = pd.ExcelWriter(result_dir)
combine_all_mtr_options = pd.merge(realtime_all_mtr_options, all_mtr_options,how = 'left',on = ['Maturity', 'Strike',
                                                                                               'CallPut'])
combine_all_mtr_options['ValueType'] = combine_all_mtr_options.apply(ValueType_define, axis = 1)
combine_mtr_options = combine_all_mtr_options.groupby(['Maturity'])

mtr_count = 0
for mtr, mtr_group in combine_mtr_options:
    mtr_cp_group = mtr_group.groupby(['CallPut'])
    group_count = 0
    for cp, cp_group in mtr_cp_group:
        cp_group = cp_group.sort_values(by='Strike')
        if group_count == 0:
            daily_group = cp_group
        else:
            daily_group = pd.merge(daily_group, cp_group, how='outer', on=['Maturity', 'Strike', 'underlying_index'])
        group_count += 1
    mtr_cp_df = daily_group.loc[:, ['ValueType_x','bid_iv_x','m_bid_vol_x','best_bid_price_x','m_bid_x','best_ask_price_x','m_ask_x','ask_iv_x',
                                    'm_ask_vol_x','delta_x','m_delta_x','Strike','delta_y','m_delta_y','bid_iv_y',
                                    'm_bid_vol_y','best_bid_price_y','m_bid_y','best_ask_price_y','m_ask_y','ask_iv_y','m_ask_vol_y', 'ValueType_y']]
    mtr_cp_df.columns = ['ValueType_x','bid_iv_c','m_bid_vol_c','bid_1_c','m_bid_c','ask_1_c','m_ask_c','ask_iv_c',
                         'm_ask_vol_c','delta_c','m_delta_c','Strike','delta_p','m_delta_p','bid_iv_p',
                         'm_bid_vol_p','bid_1_p','m_bid_p','ask_1_p','m_ask_p','ask_iv_p','m_ask_vol_p','ValueType_y']

    mtr_cp_df.to_excel(writer, sheet_name=str(mtr), index=False)
    if mtr_count == 0:
        all_data = daily_group
    else:
        all_data = all_data.append(daily_group)
    mtr_count += 1
writer.save()

#plot surface and smile
surface_data = combine_all_mtr_options.loc[combine_all_mtr_options['ValueType'] == 'OTM']
surface_data['Maturityint'] = surface_data['Maturity'].apply(lambda t: int(str(t).replace('-','')))

plot_dir = project_dir.implied_vol_plot_dir(date=datetime.date.today().strftime("%Y%m%d"))
pdf = PdfPages(plot_dir)
#plot the vol curve:
for i in ['mark_iv','m_mid_vol']:
    fig = plt.figure()
    ax1 = plt.axes(projection='3d')
    Vol_surface = surface_data.pivot(index = 'Maturityint',columns = 'Strike',values= i)
    X = list(set(surface_data['Maturityint']))
    Y = list(set(surface_data['Strike']))
    X.sort()
    Y.sort()
    Y,X = np.meshgrid(Y, X)
    ax1.plot_surface(X,Y,Vol_surface)
    ax1.contourf(X, Y, Vol_surface,
                zdir='z',
                offset=-2,
                )
    if i == 'mark_iv':
        fig.suptitle('Realtime Vol Surface')
    else:
        fig.suptitle('My Vol Surface')
    pdf.savefig()
    plt.close()

all_data_mtr = all_data.groupby('Maturity')
ATM_option = pd.DataFrame()
for mtr,mtr_group in all_data_mtr:
    underlying_strike = mtr_group['underlying_price_x_x']
    strike_list = abs(mtr_group['Strike']-underlying_strike)
    min_index = strike_list.idxmin()
    ATM_option = ATM_option.append(mtr_group.loc[min_index,:])
# ATM call
plt.figure(figsize=(6, 6))
fig = plt.figure(1)
ax1 = plt.subplot(311)
ax1.plot(ATM_option['Maturity'],ATM_option['bid_iv_x'],'.-')
ax1.plot( ATM_option['Maturity'],ATM_option['m_bid_vol_x'],'.-')
ax1.legend(loc='upper right')
ax1.set_ylim((-2,2))
ax3 = plt.subplot(312)
ax3.plot(ATM_option['Maturity'],ATM_option['ask_iv_x'],'.-')
ax3.plot(ATM_option['Maturity'],ATM_option['m_ask_vol_x'],'.-')
ax3.legend(loc='upper right')
ax3.set_ylim((-2,2))
ax5 = plt.subplot(313)
ax5.plot(ATM_option['Maturity'],ATM_option['mark_iv_x'],'.-')
ax5.plot(ATM_option['Maturity'],ATM_option['m_mid_vol_x'],'.-')
ax5.legend(loc='upper right')
ax5.set_ylim((-2,2))
fig.suptitle('ATM Call Vol Term Structure')
pdf.savefig()
plt.close()
# ATM put
plt.figure(figsize=(6, 6))
fig = plt.figure(1)
ax2 = plt.subplot(311)
ax2.plot(ATM_option['Maturity'],ATM_option['bid_iv_y'],'.-')
ax2.plot(ATM_option['Maturity'],ATM_option['m_bid_vol_y'],'.-')
ax2.legend(loc='upper right')
ax2.set_ylim((-2,2))
ax4 = plt.subplot(312)
ax4.plot(ATM_option['Maturity'],ATM_option['ask_iv_y'],'.-')
ax4.plot(ATM_option['Maturity'],ATM_option['m_ask_vol_y'],'.-')
ax4.legend(loc='upper right')
ax4.set_ylim((-2,2))
ax6 = plt.subplot(313)
ax6.plot(ATM_option['Maturity'],ATM_option['mark_iv_y'],'.-')
ax6.plot(ATM_option['Maturity'],ATM_option['m_mid_vol_y'],'.-')
ax6.legend(loc='upper right')
ax6.set_ylim((-2,2))
fig.suptitle('ATM Put Vol Term Structure')
pdf.savefig()
plt.close()
for mtr,mtr_group in all_data_mtr:
    plt.figure(figsize=(6, 6))
    fig = plt.figure(1)
    ax1 = plt.subplot(321)
    ax1.plot(mtr_group['Strike'],mtr_group['bid_iv_x'],'.-')
    ax1.plot(mtr_group['Strike'],mtr_group['m_bid_vol_x'],'.-')
    ax1.set_title('Call Bid Vol')
    ax1.legend(loc = 'upper right')

    ax2 = plt.subplot(322)
    ax2.plot(mtr_group['Strike'], mtr_group['bid_iv_y'],'.-')
    ax2.plot(mtr_group['Strike'],mtr_group['m_bid_vol_y'],'.-')
    ax2.set_title('Put Bid Vol')
    ax2.legend(loc = 'upper right')

    ax3 = plt.subplot(323)
    ax3.plot(mtr_group['Strike'],mtr_group['ask_iv_x'],'.-')
    ax3.plot(mtr_group['Strike'],mtr_group['m_ask_vol_x'],'.-')
    ax3.set_title('Call Ask Vol')
    ax3.legend(loc = 'upper right')

    ax4 = plt.subplot(324)
    ax4.plot(mtr_group['Strike'],mtr_group['ask_iv_y'],'.-')
    ax4.plot(mtr_group['Strike'],mtr_group['m_ask_vol_y'],'.-')
    ax4.set_title('Put Ask Vol')
    ax4.legend(loc = 'upper right')

    ax5 = plt.subplot(325)
    ax5.plot(mtr_group['Strike'], mtr_group['mark_iv_x'],'.-')
    ax5.plot(mtr_group['Strike'], mtr_group['m_mid_vol_x'],'.-')
    ax5.set_title('Call Mid Vol')
    ax5.legend(loc = 'upper right')

    ax6 = plt.subplot(326)
    ax6.plot(mtr_group['Strike'], mtr_group['mark_iv_y'],'.-')
    ax6.plot(mtr_group['Strike'], mtr_group['m_mid_vol_y'],'.-')
    ax6.set_title('Put Mid Vol')
    ax6.legend(loc = 'upper right')

    plt.tight_layout()
    fig.suptitle(str(mtr))
    pdf.savefig()
    plt.close()
pdf.close()







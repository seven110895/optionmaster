import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
from scipy import interpolate
from matplotlib.backends.backend_pdf import PdfPages


all_mtr_options = pd.read_csv("D:/optionmaster/Straddle/Straddle_vol/ALL_MTR_STRIKE.csv")
#all_mtr_options = all_mtr_options.replace(-1,np.nan)

mtr_count = 0
vol_df_mtr = all_mtr_options.groupby('Date')
for mtr,mtr_group in vol_df_mtr:
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

    if mtr_count ==0:
        all_ATM_Call_df = ATM_Call_df
        all_ATM_Put_df = ATM_Put_df
        all_ATM_df = ATM_Vol_df
    else:
        all_ATM_Call_df = all_ATM_Call_df.append(ATM_Call_df)
        all_ATM_Put_df  = all_ATM_Put_df.append(ATM_Put_df)
        all_ATM_df = all_ATM_df.append(ATM_Vol_df)
    mtr_count += 1

all_ATM_df['ValueType'] = 'ATM'
all_ATM_df['Maturity'] = all_ATM_df['Maturity'].apply(lambda x:np.datetime64(x).astype(datetime.date))
all_ATM_df['Date'] = all_ATM_df['Date'].apply(lambda x:np.datetime64(x).astype(datetime.date))
all_ATM_df['time_to_maturity'] = all_ATM_df['Maturity'] - all_ATM_df['Date']
all_ATM_df['time_to_maturity'] = all_ATM_df['time_to_maturity'].apply(lambda x: int(x.days))
all_ATM_df_C = all_ATM_df.loc[all_ATM_df['CallPut'] == 'C', :]
ATM_Vol_C_groupby_ttm = all_ATM_df_C.pivot(index='Date', columns='time_to_maturity', values='m_mid_vol')
ATM_Vol_C_groupby_ttm = ATM_Vol_C_groupby_ttm.replace(-1, np.nan)
ATM_Vol_daily = ATM_Vol_C_groupby_ttm.groupby('Date')
ttm_list = np.array(ATM_Vol_C_groupby_ttm.columns)
all_ATM_df_C.to_csv('D:/optionmaster/Trade_plot/ATM_information.csv')
pdf = PdfPages("D:/optionmaster/Straddle/Vol_plot/ATM_vol_term_structure_V3_interpolate.pdf")
Vol_interpolate = pd.DataFrame(columns=np.arange(1, max(ttm_list)+1))
for date, date_group in ATM_Vol_daily:
    nona_date_group = date_group.dropna(axis=1)
    ttm = np.array(nona_date_group.columns)
    vol = np.array(nona_date_group.iloc[0, :])
    vol_square = [x**2 for x in vol]
    f = interpolate.interp1d(ttm, vol_square, kind = 'linear')

    ttm_list = np.arange(min(ttm), max(ttm)+1)
    vol_square_new = f(ttm_list)
    vol_new = [np.sqrt(x) for x in vol_square_new]
    Vol_interpolate.loc[date, min(ttm):max(ttm)] = vol_new

    plt.figure(figsize=(6, 6))
    fig = plt.figure(1)
    ax1 = plt.subplot(111)
    ax1.plot(ttm_list, vol_new)
    ax1.scatter(ttm, vol)
    ax1.set_xlabel('Time to Maturity (days)')
    ax1.set_xlim(0, max(ttm_list))
    ax1.set_ylim(0.4,1)
    ax1.set_title(str(date) + 'ATM Vol Term Structure')
    pdf.savefig()
    plt.close()
pdf.close()
Vol_interpolate.to_csv("D:/optionmaster/Straddle/Vol_plot/ATM_vol_term_structure_V3_interpolate.csv")

vol_fit = pd.DataFrame(columns= np.arange(1,250,1))
pdf = PdfPages("D:/optionmaster/Straddle/Vol_plot/ATM_vol_term_structure_V3_fit.pdf")
for date, date_group in ATM_Vol_daily:
    nona_date_group = date_group.dropna(axis=1)
    ttm = np.array(nona_date_group.columns)
    vol = np.array(nona_date_group.iloc[0, :])
    ttm_list = np.arange(1,250,1)
    f1 = np.polyfit(ttm, vol, 2)
    yvals = np.polyval(f1,ttm_list)
    vol_fit.loc[date,:] = yvals

    plt.figure(figsize=(6, 6))
    fig = plt.figure(1)
    ax1 = plt.subplot(111)
    ax1.plot(ttm_list, yvals)
    ax1.scatter(ttm,vol)
    ax1.set_xlabel('Time to Maturity (days)')
    ax1.set_ylim(0.4, 1)
    ax1.set_title(str(date) + 'ATM Vol Term Structure')
    pdf.savefig()
    plt.close()
pdf.close()


pdf = PdfPages("D:/optionmaster/Straddle/Vol_plot/ATM_vol_term_structure_V3_fit_trend.pdf")
plt.figure(figsize=(6, 6))
fig = plt.figure(1)
ax1 = plt.subplot(111)
ax1.plot(vol_fit.index, vol_fit.loc[:,1],label = '1-day Vol')
ax1.plot(vol_fit.index, vol_fit.loc[:,15],label = '15-day Vol')
ax1.plot(vol_fit.index, vol_fit.loc[:,60],label = '60-day Vol')
ax1.legend(loc='best')
ax1.set_title('Vol change trend')
pdf.savefig()
plt.close()
pdf.close()
vol_fit_day = vol_fit.loc[:,[1,5,15,30,60,180]]
vol_fit_day.columns = ['1-day-vol','5-day-vol','15-day-vol','30-day-vol','60-day-vol','180-day-vol']
vol_fit_day.to_csv("D:/optionmaster/Straddle/Vol_plot/ATM_vol_term_structure_V3_fit.csv")

mtr_count = 0
pdf = PdfPages("D:/optionmaster/Straddle/Vol_plot/ATM_vol_term_structure_V2.pdf")
vol_df_mtr = all_mtr_options.groupby('Date')
for mtr,mtr_group in vol_df_mtr:
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

    if mtr_count ==0:
        all_ATM_Call_df = ATM_Call_df
        all_ATM_Put_df = ATM_Put_df
        all_ATM_df = ATM_Vol_df
    else:
        all_ATM_Call_df = all_ATM_Call_df.append(ATM_Call_df)
        all_ATM_Put_df  = all_ATM_Put_df.append(ATM_Put_df)
        all_ATM_df = all_ATM_df.append(ATM_Vol_df)
    mtr_count += 1

    plt.figure(figsize=(6, 6))
    fig = plt.figure(1)
    ax1 = plt.subplot(211)
    ax1.plot(ATM_Call_df['Maturity'],ATM_Call_df['m_bid_vol'], '.-', label = 'bid_vol')
    ax1.plot(ATM_Call_df['Maturity'], ATM_Call_df['m_ask_vol'], '.-', label = 'ask_vol')
    ax1.plot(ATM_Call_df['Maturity'], ATM_Call_df['m_mid_vol'], '.-', label = 'mid_vol')
    ax1.legend(loc='best')
    ax1.set_ylim((0.4,1))
    ax1.set_title(str(mtr) +' ATM Call Vol Term Structure')

    ax2 = plt.subplot(212)
    ax2.plot(ATM_Put_df['Maturity'], ATM_Put_df['m_bid_vol'], '.-', label = 'bid_vol')
    ax2.plot(ATM_Put_df['Maturity'], ATM_Put_df['m_ask_vol'], '.-', label = 'ask_vol')
    ax2.plot(ATM_Put_df['Maturity'], ATM_Put_df['m_mid_vol'], '.-', label = 'mid_vol')
    ax2.legend(loc='best')
    ax2.set_ylim((0.4, 1))
    ax2.set_title( str(mtr) + ' ATM Put Vol Term Structure')

    plt.tight_layout()
    pdf.savefig()
    plt.close()
pdf.close()

all_ATM_df['ValueType'] = 'ATM'
all_ATM_df = all_ATM_df.iloc[:,1::]
all_ATM_df.to_csv("D:/optionmaster/Straddle/Vol_plot/ATM_vol_term_structure.csv")
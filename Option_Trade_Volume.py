import os
import pandas as pd
import re
import datetime
import matplotlib.pyplot as plt
from change_directory import directory
from matplotlib.backends.backend_pdf import PdfPages


def change_maturity(mtr):
    month_list = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    mtr = re.split('([A-Z]+)', mtr)
    month = month_list.index(mtr[1]) + 1
    maturity = datetime.date(int(mtr[2]) + 2000, month, int(mtr[0]))
    return maturity

def find_maturity(row):
    ATM_df = pd.read_csv("D:\\optionmaster\\Trade_plot\\ATM_information.csv")
    temp_df = ATM_df.loc[ATM_df['Date'] == str(row['Date']), :]
    temp_df = temp_df.loc[temp_df['Maturity'] == str(row['Maturity']), :]
    underlying = temp_df['underlying_price']
    return float(underlying)


ATM_df = pd.read_csv("D:\\optionmaster\\Trade_plot\\ATM_information.csv")
# Get all trade data from directory.
project_dir = directory()
trade_folder_dir = project_dir.trade_folder_dir()
fileList = os.listdir(trade_folder_dir)

startDate = datetime.date(2020, 2, 1)
endDate = datetime.date(2020, 2, 8)
day_count = 0
for i in fileList:

    fileDate = re.split('(\d{4})(\d{2})(\d{2})', i)
    year = int(fileDate[1])
    month = int(fileDate[2])
    day = int(fileDate[3])
    date = datetime.date(year, month, day)
    date_str =  datetime.date(year, month, day).strftime("%Y%m%d")
    if startDate <= date <= endDate:
        readFileDir = project_dir.trade_dir(date_str)
        tradeData = pd.read_csv(filepath_or_buffer=readFileDir)
        option_index = []
        for row in tradeData.iterrows():
            instrument = row[1]['instrument']
            instr_to_list = instrument.split('-')
            if instr_to_list[0] == 'BTC' and len(instr_to_list) == 4:
                option_index.append(row[0])
        option_trade_df = tradeData.iloc[option_index,:]
        option_trade_df['CallPut'] = option_trade_df['instrument'].apply(lambda x:x.split('-')[3])
        option_trade_df_C = option_trade_df[option_trade_df['CallPut'] == 'P']


        mtr_option_trade_df = option_trade_df_C.groupby(['instrument']).agg({'side':'count','quantity':'sum'})
        mtr_option_trade_df = mtr_option_trade_df.reset_index()
        mtr_option_trade_df['Date'] = str(date)
        mtr_option_trade_df['Strike'] = mtr_option_trade_df['instrument'].apply(lambda x: x.split('-')[2])
        mtr_option_trade_df['Maturity']= mtr_option_trade_df['instrument'].apply(lambda x: x.split('-')[1])
        mtr_option_trade_df['Maturity'] = mtr_option_trade_df['Maturity'].apply(change_maturity)
        mtr_option_trade_df['Maturity'] = mtr_option_trade_df['Maturity'].apply(str)
        mtr_option_trade_df = pd.merge(mtr_option_trade_df, ATM_df.loc[:,["Date","Maturity","underlying_price"]], how = 'left',on = ['Date','Maturity'] )
        mtr_option_trade_df = mtr_option_trade_df.dropna()
        mtr_option_trade_df['Moneyness'] = mtr_option_trade_df['underlying_price'] / mtr_option_trade_df['Strike'].apply(float)

        if day_count == 0:
            all_trade_data = mtr_option_trade_df
        else:
            all_trade_data = all_trade_data.append(mtr_option_trade_df)
        print('finish' + str(date))
        day_count += 1
all_trade_data = all_trade_data.sort_values(['Date','Maturity','quantity'])
data_all = all_trade_data.loc[:,['Date','instrument','Maturity','Strike','Moneyness','quantity']]
data_all.to_csv("D:\\optionmaster\\Trade_plot\\Put_Trade_Vol.csv")


all_trade_data.to_csv('D:/optionmaster/Trade_plot/Trade_volume.csv')
#all_trade_data = pd.read_csv('D:/optionmaster/Trade_plot/Trade_volume.csv')
all_trade_data['Strike'] = all_trade_data['instrument'].apply(lambda x:float(x.split('-')[2]))
all_trade_data['Maturity'] = all_trade_data['instrument'].apply(lambda x:x.split('-')[1])
all_trade_data['Maturity'] = all_trade_data['Maturity'].apply(change_maturity)
all_trade_data_by_mtr = all_trade_data.groupby(['Date','Maturity','Strike']).agg(sum)
all_trade_data_by_mtr = all_trade_data_by_mtr.reset_index()
all_trade_data_by_mtr = all_trade_data_by_mtr.sort_values(['Date','Maturity','Strike'])

#ATM_options = pd.read_csv("D:/optionmaster/Straddle/Straddle_vol/Oct_atm.csv")
#all_trade_data_by_mtr = pd.merge(all_trade_data_by_mtr, ATM_options.loc[:, ['Date', 'Maturity', 'Strike','ValueType']], how = 'left' )

daily_trade_data = all_trade_data_by_mtr.groupby('Date')
pdf = PdfPages("D:/optionmaster/Trade_plot/Trade_Volume_Plot.pdf")
for day, daily_group in daily_trade_data:
    mtr_num = len(set(daily_group['Maturity']))
    plt.figure(figsize=(6, 10))
    fig = plt.figure(1)
    ax1 = fig.subplots(mtr_num,1)
    daily_group_by_mtr = daily_group.groupby('Maturity')
    fig_count = 0
    for mtr, mtr_group in daily_group_by_mtr:
        ax1[fig_count].plot(mtr_group['Strike'], mtr_group['side'],'.-',label = str(mtr))
        ax1[fig_count].set_title('Maturity:' + str(mtr),loc='left')
        fig_count +=1
    plt.suptitle('Trade_day:' + str(day))
    plt.tight_layout()
    pdf.savefig()
    plt.close()
pdf.close()




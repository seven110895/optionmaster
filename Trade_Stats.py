import os
import pandas as pd
import re
import matplotlib.pyplot as plt
import datetime

from change_directory import directory

# Get all trade data from directory.
project_dir = directory
trade_folder_dir = project_dir.trade_folder_dir()
fileList = os.listdir(trade_folder_dir)
for i in fileList:

    fileDate = re.split('(\d{4})(\d{2})(\d{2})', i)
    year = int(fileDate[1])
    month = int(fileDate[2])
    day = int(fileDate[3])
    timestampString, timestamp, side, price, quantity, currency, maturity, strike, callput, realTime, hourList, callPutSide = [], [], [], [], [], [], [], [], [], [], [], []
    group_15min, timeList = [], []
    perpTime, perpPrice, perpRealTime, perpTimeString, perpQuantity = [], [], [], [], []
    futureList = []
    futureTime, futurePrice, futureQuantity, futureTimeString = [], [], [], []
    date = datetime.date(year, month, day).strftime("%Y%m%d")
    # Prepare to save figure to directory.
    figDir = project_dir.trade_quantity_plot_dir(date)
    if not os.path.isfile(figDir):
        readFileDir = project_dir.trade_dir(date)
        tradeData = pd.read_csv(filepath_or_buffer=readFileDir)

        for row in tradeData.iterrows():
            instrument = row[1]['instrument']
            instr_to_list = instrument.split('-')
            if instr_to_list[0] == 'BTC' and len(instr_to_list) == 4:
                time = row[1]['timestamp']
                hour = int(re.split('[T](\d+)', time)[1])
                timeRemaining = re.split('[:](\d+)', time)
                minute = int(timeRemaining[1])
                second = int(timeRemaining[3])
                ms = int(re.split('(\d+)', timeRemaining[4])[1])
                timeNum = hour * 60 * 60 + minute * 60 + second + ms / 1000
                timestamp.append(timeNum)
                t15 = int(timeNum / (15 * 60))
                group_15min.append(t15)
                rTime = datetime.datetime(year, month, day, hour, minute, second, ms * 1000)
                rTimeStr = rTime.strftime("%Y/%m/%d-%H:%M:%S.%f")
                timestampString.append(rTimeStr)
                realTime.append(rTime)
                thisHour = datetime.datetime(year, month, day, hour, 0, 0, 0)
                hourList.append(thisHour)
                t_l = datetime.time(hour, 0, 0)
                timeList.append(t_l)
                side.append(row[1]['side'])
                price.append(row[1]['price'])
                cp_side = instr_to_list[3] + '_' + row[1]['side']
                callPutSide.append(cp_side)
                quantity.append(row[1]['quantity'])
                currency.append(instr_to_list[0])
                maturity.append(instr_to_list[1])
                strike.append(instr_to_list[2])
                callput.append(instr_to_list[3])
            elif instr_to_list[0] == 'BTC' and instr_to_list[1] == 'PERPETUAL':
                time = row[1]['timestamp']
                hour = int(re.split('[T](\d+)', time)[1])
                timeRemaining = re.split('[:](\d+)', time)
                minute = int(timeRemaining[1])
                second = int(timeRemaining[3])
                ms = int(re.split('(\d+)', timeRemaining[4])[1])
                timeNum = hour * 60 * 60 + minute * 60 + second + ms / 1000
                perpTime.append(timeNum)
                rTime = datetime.datetime(year, month, day, hour, minute, second, ms * 1000)
                rTimeStr = rTime.strftime("%Y/%m/%d-%H:%M:%S.%f")
                perpTimeString.append(rTimeStr)
                perpRealTime.append(rTime)
                perpPrice.append(row[1]['price'])
                perpQuantity.append(row[1]['quantity'])
            elif len(instr_to_list) == 2 and instr_to_list[0] == 'BTC' and not instr_to_list[1] == 'PERPETUAL':
                if instr_to_list[1] in futureList:
                    futureIndex = futureList.index(instr_to_list[1])
                    fTime = futureTime[futureIndex]
                    fPrice = futurePrice[futureIndex]
                    fQuantity = futureQuantity[futureIndex]
                    fTimeString = futureTimeString[futureIndex]
                    time = row[1]['timestamp']
                    hour = int(re.split('[T](\d+)', time)[1])
                    timeRemaining = re.split('[:](\d+)', time)
                    minute = int(timeRemaining[1])
                    second = int(timeRemaining[3])
                    ms = int(re.split('(\d+)', timeRemaining[4])[1])
                    timeNum = hour * 60 * 60 + minute * 60 + second + ms / 1000
                    rTime = datetime.datetime(year, month, day, hour, minute, second, ms * 1000)
                    fTime.append(rTime)
                    rTimeStr = rTime.strftime("%Y/%m/%d-%H:%M:%S.%f")
                    fTimeString.append(rTimeStr)
                    fPrice.append(row[1]['price'])
                    fQuantity.append(row[1]['quantity'])
                    futureTimeString[futureIndex] = fTimeString
                    futureTime[futureIndex] = fTime
                    futureQuantity[futureIndex] = fQuantity
                    futurePrice[futureIndex] = fPrice
                else:
                    futureList.append(instr_to_list[1])
                    fTime, fPrice, fQuantity, fTimeString = [], [], [], []
                    time = row[1]['timestamp']
                    hour = int(re.split('[T](\d+)', time)[1])
                    timeRemaining = re.split('[:](\d+)', time)
                    minute = int(timeRemaining[1])
                    second = int(timeRemaining[3])
                    ms = int(re.split('(\d+)', timeRemaining[4])[1])
                    timeNum = hour * 60 * 60 + minute * 60 + second + ms / 1000
                    rTime = datetime.datetime(year, month, day, hour, minute, second, ms * 1000)
                    fTime.append(rTime)
                    rTimeStr = rTime.strftime("%Y/%m/%d-%H:%M:%S.%f")
                    fTimeString.append(rTimeStr)
                    fPrice.append(row[1]['price'])
                    fQuantity.append(row[1]['quantity'])
                    futureTime.append(fTime)
                    futurePrice.append(fPrice)
                    futureQuantity.append(fQuantity)
                    futureTimeString.append(fTimeString)

        futureCount = []
        for f in range(0, len(futureList)):
            futureCount.append(0)

        pairedFuturePrice, pairedPerpetualPrice = [], []
        perpetualCount = 0
        for p in range(0, len(futureList)):
            pairedFuturePrice.append([])

        for i in range(0, len(realTime)):
            for j in range(0, len(futureList)):
                fTime = futureTime[j]
                fCount = futureCount[j]
                fPrice = futurePrice[j]
                fQuantity = futureQuantity[j]
                while fTime[fCount] < realTime[i] and fCount < len(fPrice) - 1:
                    fCount += 1
                if fCount == 0:
                    f_price = fPrice[fCount]
                    futureCount[j] = fCount
                else:
                    f_price = fPrice[fCount - 1]
                    futureCount[j] = fCount - 1
                pairedFuturePrice[j].append(f_price)
            while perpRealTime[perpetualCount] < realTime[i] and perpetualCount < len(perpRealTime) - 1:
                perpetualCount += 1
            if perpetualCount == 0:
                p_price = perpPrice[perpetualCount]
            else:
                p_price = perpPrice[perpetualCount - 1]
            pairedPerpetualPrice.append(p_price)

        btc_trades_data = {'Time': timestampString, 'Hour': hourList, '15MinGroup': group_15min, 'Time_Only': timeList,
                           'Side': side, 'Price': price, 'Quantity': quantity, 'Currency': currency,
                           'Maturity': maturity, 'Strike': strike, 'CallPut': callput, 'CallPut_Side': callPutSide}
        btc_trades = pd.DataFrame(btc_trades_data)

        formalData = {'Time': timestampString, 'Currency': currency, 'Maturity': maturity, 'CallPut': callput,
                      'Strike': strike, 'Side': side, 'Price': price, 'Quantity': quantity}
        # Save option trade result to csv.
        dataDir = project_dir.trade_stats_file_dir(date, 'option')
        formalDF = pd.DataFrame(formalData)
        formalDF['PerpetualPrice'] = pairedPerpetualPrice
        for i in range(0, len(futureList)):
            f_mtr = futureList[i]
            formalDF[f_mtr] = pairedFuturePrice[i]
            futureData = {'Time': futureTimeString[i], 'Price': futurePrice[i], 'Quantity': futureQuantity[i]}
            futureDF = pd.DataFrame(futureData)
            # Save future trade result to csv.
            futureDir = project_dir.trade_stats_file_dir(date, 'future')
            futureDF.to_csv(path_or_buf=futureDir)

        formalDF.to_csv(path_or_buf=dataDir)
        perpData = {'Time': perpTimeString, 'Price': perpPrice, 'Quantity': perpQuantity}
        perpDF = pd.DataFrame(perpData)
        # Save perpetual trade result to csv.
        perpDir = project_dir.trade_stats_file_dir(date, 'perpetual')
        perpDF.to_csv(path_or_buf=perpDir)

        fig, ax1 = plt.subplots(2, 1)
        titleDate = datetime.date(year, month, day).strftime("%Y/%m/%d")
        figTitle = 'Option Trades: ' + titleDate
        fig.suptitle(figTitle)
        fig.set_size_inches(18.5, 10.5, forward=True)
        btc_trades.groupby(['Time_Only', 'CallPut_Side'])['Quantity'].sum().unstack().plot(kind='bar', ax=ax1[1])
        ax1[1].set(xlabel='Time (Group by Hour)', ylabel='Trading Volume (Contracts on 1 BTC)')
        ax1[1].set_title('Option Trading Volume')
        ax1[0].plot(perpRealTime, perpPrice, 'k')
        ax1[0].set_xlim(
            [realTime[0], datetime.datetime(year, month, day, 0, 0, 0, 0) + datetime.timedelta(1)])
        ax1[0].set(xlabel='Time', ylabel='Perpetual Price')
        ax1[0].set_title('Perpetual Price')
        plt.savefig(figDir, quality=95, orientation='landscape', papertype='letter')
        # plt.show()
    print('Finished trades: ', date, '!')

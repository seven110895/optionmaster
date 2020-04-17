from DataClient import DataClient
import pandas as pd
import datetime
import re

class get_data:
    def __init__(self, f):
        client = DataClient('3.17.63.79', 22, 'ec2-user', 'Waa9b25xyk')
        client.connect()
        self.dataFile=client.getfile(f)
        self.fileName=f

    def to_dataframe(self):
        orderbookFile=self.dataFile.split("\n")
        dataLength=len(orderbookFile)
        price=[]
        time=[]
        lineCount=0
        for row in orderbookFile:
            if lineCount != 0 and lineCount < dataLength - 1:
                line = row.split(',')
                prc = (float(line[1]) + float(line[11])) / 2
                price.append(prc)
                timestamp = line[0].split("T")
                timestamp = timestamp[1].strip("Z").split(":")
                s = timestamp[2].split(".")
                t = int(timestamp[0]) * 60 * 60 + int(timestamp[1]) * 60 + int(s[0]) + (int(s[1])) / 1000
                if t > 86300 and lineCount < 300:
                    t = t - 86400
                time.append(t)
            lineCount += 1
        result={'Time': time, 'Price': price}
        resultDF=pd.DataFrame(result)
        return resultDF

    def all_to_dataframe(self):
        orderbookFile=self.dataFile.split("\n")
        dataLength=len(orderbookFile)
        time=[]
        bp1, bp2, bp3, bp4, bp5 = [], [], [], [], []
        bq1, bq2, bq3, bq4, bq5 = [], [], [], [], []
        ap1, ap2, ap3, ap4, ap5 = [], [], [], [], []
        aq1, aq2, aq3, aq4, aq5 = [], [], [], [], []
        lineCount=0
        f_to_list=self.fileName.split('-')
        dateString = re.split('_(\d{4})(\d{2})(\d{2})', f_to_list[4])
        for row in orderbookFile:
            if lineCount != 0 and lineCount < dataLength - 1:
                # print(row)
                line = row.split(',')
                timestamp = line[0].split("T")
                timestamp = timestamp[1].strip("Z").split(":")
                s = timestamp[2].split(".")
                t=datetime.datetime(int(dateString[1]), int(dateString[2]), int(dateString[3]), int(timestamp[0]), int(timestamp[1]), int(s[0]), int(s[1])*1000)
                time.append(t.strftime("%Y/%m/%d-%H:%M:%S.%f"))
                bp1.append(float(line[1]))
                bq1.append(float(line[2]))
                bp2.append(float(line[3]))
                bq2.append(float(line[4]))
                bp3.append(float(line[5]))
                bq3.append(float(line[6]))
                bp4.append(float(line[7]))
                bq4.append(float(line[8]))
                bp5.append(float(line[9]))
                bq5.append(float(line[10]))
                ap1.append(float(line[11]))
                aq1.append(float(line[12]))
                ap2.append(float(line[13]))
                aq2.append(float(line[14]))
                ap3.append(float(line[15]))
                aq3.append(float(line[16]))
                ap4.append(float(line[17]))
                aq4.append(float(line[18]))
                ap5.append(float(line[19]))
                aq5.append(float(line[20]))
            lineCount+=1
        resultData={'Time': time, 'Bid_1_Price':bp1, 'Bid_1_Quantity': bq1, 'Bid_2_Price':bp2, 'Bid_2_Quantity': bq2,
                    'Bid_3_Price':bp3, 'Bid_3_Quantity': bq3, 'Bid_4_Price':bp4, 'Bid_4_Quantity': bq4,
                    'Bid_5_Price':bp5, 'Bid_5_Quantity': bq5, 'Ask_1_Price':ap1, 'Ask_1_Quantity': aq1,
                    'Ask_2_Price':ap2, 'Ask_2_Quantity': aq2, 'Ask_3_Price':ap3, 'Ask_3_Quantity': aq3,
                    'Ask_4_Price':ap4, 'Ask_4_Quantity': aq4, 'Ask_5_Price':ap5, 'Ask_5_Quantity': aq5}
        resultDF=pd.DataFrame(resultData)
        return resultDF
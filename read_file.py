from DataClient import DataClient
import pandas as pd
import datetime
import re
import numpy as np

class get_data:
    def __init__(self, f):
        try:
            self.dataFile = pd.read_csv(f)
        except:
            df = pd.read_csv(f, header=None, sep='\n')
            df = df[0].str.split(',', expand=True)
            new_header = df.iloc[0].fillna(df.columns.to_series())
            df = df[1:]
            df.columns = new_header
            df = df.reset_index(drop=True)
            self.dataFile = df
        self.fileName=f

    def to_dataframe(self):
        price=[]
        time=[]
        lineCount=0
        for i in np.arange(len(self.dataFile)):
            timestamp = self.dataFile["timestamp"][i].split("T")
            if len(timestamp) !=2 :

                continue
            timestamp = timestamp[1].strip("Z").split(":")
            s = timestamp[2].split(".")
            t = int(timestamp[0]) * 60 * 60 + int(timestamp[1]) * 60 + int(s[0]) + (int(s[1])) / 1000
            if t > 86300 and lineCount < 300:
                t = t - 86400
            time.append(t)

            prc = (self.dataFile["bid1_price"][i]+self.dataFile["ask1_price"][i])/2
            price.append(prc)
            lineCount += 1
        result = {'Time': time, 'Price': price}
        resultDF = pd.DataFrame(result)
        return resultDF


    def all_to_dataframe(self):

        time=[]
        bp1, bp2, bp3, bp4, bp5 = [], [], [], [], []
        bq1, bq2, bq3, bq4, bq5 = [], [], [], [], []
        ap1, ap2, ap3, ap4, ap5 = [], [], [], [], []
        aq1, aq2, aq3, aq4, aq5 = [], [], [], [], []
        lineCount=0
        f_to_list=self.fileName.split('-')
        dateString = re.split('_(\d{4})(\d{2})(\d{2})', f_to_list[4])


        for i in np.arange(len(self.dataFile)):
            timestamp = self.dataFile["timestamp"][i].split("T")
            if len(timestamp) !=2 :
                time.append(0)
                continue
            timestamp = timestamp[1].strip("Z").split(":")
            s = timestamp[2].split(".")
            t = datetime.datetime(int(dateString[1]), int(dateString[2]), int(dateString[3]), int(timestamp[0]),
                                  int(timestamp[1]), int(s[0]), int(s[1]) * 1000)
            time.append(t.strftime("%Y/%m/%d-%H:%M:%S.%f"))
        resultData = self.dataFile.iloc[:, 0:21]
        resultData["timestamp"] = time
        resultData.columns = ['Time', 'Bid_1_Price', 'Bid_1_Quantity', 'Bid_2_Price',
                      'Bid_2_Quantity','Bid_3_Price', 'Bid_3_Quantity', 'Bid_4_Price', 'Bid_4_Quantity',
                      'Bid_5_Price', 'Bid_5_Quantity', 'Ask_1_Price', 'Ask_1_Quantity',
                      'Ask_2_Price', 'Ask_2_Quantity', 'Ask_3_Price', 'Ask_3_Quantity',
                      'Ask_4_Price', 'Ask_4_Quantity', 'Ask_5_Price', 'Ask_5_Quantity']

        return resultData


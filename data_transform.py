import pandas as pd
import re
import os
import calendar
import datetime
import numpy as np
import shutil
from DataClient import DataClient
from read_file import get_data
from change_directory import directory


def data_transform(start_date,end_date):
    output_dir=directory()
    date_dir = os.listdir("D:/deri-bit/")
    datelist = []
    for t in date_dir:
        temp = datetime.datetime.strptime(t,'%Y%m%d').date()
        datelist.append(temp)

    for d in np.arange(start_date, end_date):
        date = np.datetime64(d).astype(datetime.date)
        # Initiate the underlying values
        if d in datelist:
            arrList = "D:/deri-bit/" + str(date).replace("-","")
            arr_all = os.listdir(arrList)
            arr=[]
            for f in arr_all:
                f_1 = f.split("-")
                if f_1[0] == "BTC":
                    arr.append("D:/deri-bit/"+str(date).replace("-","")+"/"+f)
            for f in arr:
                f_to_list = f.split('-')
                #  Options:
                if len(f_to_list) > 3:
                    cp_date=re.split('_(\d+)', f_to_list[4])
                    optionsDir = output_dir.data_download(type='option') + cp_date[1] + '_' + f_to_list[2] + '_' + f_to_list[3] + '_' + cp_date[0] +'.csv'
                    if not os.path.exists(optionsDir):
                        contractType = f_to_list[2].split('_')[0]
                        if not contractType.startswith('PERP'):
                            options = get_data(f)
                            optionsDF = options.all_to_dataframe()
                            optionsDF.to_csv(path_or_buf=optionsDir)

                # Perpetuals
                if len(f_to_list) == 3:
                    cp_date=re.split('_(\d+)', f_to_list[2])
                    perpetualDir = output_dir.data_download(type='perpetual') + cp_date[1] + '_'+ cp_date[0] +'.csv'
                    if not os.path.exists(perpetualDir):
                        contractType = f_to_list[2].split('_')[0]
                        if contractType.startswith('PERP'):
                            perpetual = get_data(f)
                            perpetualDF = perpetual.to_dataframe()
                            perpetualDF.to_csv(path_or_buf=perpetualDir)

                # Futures
                if len(f_to_list) == 3:
                    cp_date = re.split('_(\d+)', f_to_list[2])
                    futuresDir = output_dir.data_download(type='future') + cp_date[1] + '_' + cp_date[0] + '.csv'
                    if not os.path.exists(futuresDir):
                        contractType = f_to_list[2].split('_')[0]
                        if not contractType.startswith('PERP'):
                            futures = get_data(f)
                            futuresDF = futures.to_dataframe()
                            futuresDF.to_csv(path_or_buf=futuresDir)
                print('Finished: ', date, f)

